from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.selectors import user_has_permission
from apps.common.models import BulkAuditLog, BulkJob
from apps.common.bulk_actions.registry import get_bulk_handler


def _normalize_selection(selection):
    normalized = dict(selection)
    if normalized.get("mode") == "ids":
        normalized["ids"] = [str(item) for item in normalized.get("ids", [])]
    if normalized.get("mode") == "filter":
        filters = dict(normalized.get("filters") or {})
        if filters.get("job"):
            filters["job"] = str(filters["job"])
        normalized["filters"] = filters
    return normalized


class BulkActionService:
    @staticmethod
    def start(
        *,
        organization,
        user,
        resource,
        action,
        selection,
        payload=None,
        idempotency_key=None,
    ):
        if organization is None:
            raise ValidationError({"detail": "Organization context is required."})

        if idempotency_key:
            existing = BulkJob.objects.filter(
                organization=organization,
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                return existing

        handler = get_bulk_handler(resource, action)

        if not user_has_permission(user, organization, handler.permission):
            raise PermissionDenied(f"Permission required: {handler.permission}")

        validated_payload = handler.validate_payload(payload or {})
        queryset = handler.resolve_queryset(
            organization=organization,
            selection=selection,
            user=user,
        )
        total_count = queryset.count()
        max_items = getattr(settings, "BULK_ACTION_MAX_ITEMS", 10_000)
        if total_count == 0:
            raise ValidationError({"selection": "No records match the selection."})
        if total_count > max_items:
            raise ValidationError(
                {
                    "selection": (
                        f"Selection exceeds maximum of {max_items} records. "
                        "Narrow your filters and try again."
                    )
                }
            )

        selection_mode = selection.get("mode")
        if selection_mode not in BulkJob.SelectionMode.values:
            raise ValidationError({"selection": "Invalid selection mode."})

        normalized_selection = _normalize_selection(selection)

        job = BulkJob.objects.create(
            organization=organization,
            created_by=user,
            resource=resource,
            action=action,
            selection_mode=selection_mode,
            selection_data=normalized_selection,
            action_payload=validated_payload,
            total_count=total_count,
            idempotency_key=idempotency_key or None,
        )

        from apps.common.bulk_actions.tasks import run_bulk_job_task

        run_bulk_job_task.delay(str(job.id))
        return job

    @staticmethod
    def run_job(job_id):
        try:
            job = BulkJob.objects.select_related("organization", "created_by").get(pk=job_id)
        except BulkJob.DoesNotExist:
            return

        if job.status in {
            BulkJob.Status.COMPLETED,
            BulkJob.Status.FAILED,
            BulkJob.Status.CANCELLED,
        }:
            return

        handler = get_bulk_handler(job.resource, job.action)

        job.status = BulkJob.Status.RUNNING
        job.started_at = timezone.now()
        job.progress = 0
        job.processed_count = 0
        job.save(update_fields=["status", "started_at", "progress", "processed_count", "updated_at"])

        try:
            queryset = handler.resolve_queryset(
                organization=job.organization,
                selection=job.selection_data,
                user=job.created_by,
            )
            result = handler.execute(job=job, queryset=queryset)
            job.refresh_from_db()
            job.status = BulkJob.Status.COMPLETED
            job.progress = 100
            job.processed_count = job.total_count
            job.result = result or {}
            job.completed_at = timezone.now()
            job.error_message = ""
            job.save(
                update_fields=[
                    "status",
                    "progress",
                    "processed_count",
                    "result",
                    "completed_at",
                    "error_message",
                    "updated_at",
                ]
            )
            BulkActionService._write_audit_log(job=job, success=True)
        except Exception as exc:
            job.refresh_from_db()
            job.status = BulkJob.Status.FAILED
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save(
                update_fields=["status", "error_message", "completed_at", "updated_at"]
            )
            BulkActionService._write_audit_log(job=job, success=False, error=str(exc))
            raise

    @staticmethod
    @transaction.atomic
    def _write_audit_log(*, job, success, error=None):
        summary = {
            "success": success,
            "total_count": job.total_count,
            "processed_count": job.processed_count,
            "result": job.result,
        }
        if error:
            summary["error"] = error

        BulkAuditLog.objects.create(
            bulk_job=job,
            organization=job.organization,
            actor=job.created_by,
            resource=job.resource,
            action=job.action,
            summary=summary,
        )
