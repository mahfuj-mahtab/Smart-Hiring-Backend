from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.bulk_actions.handlers.base import BaseBulkActionHandler
from apps.jobs.models import Application
from apps.jobs.selectors import get_applications_bulk_queryset


class ApplicationsChangeStageHandler(BaseBulkActionHandler):
    permission = "candidate.change"

    def validate_payload(self, payload):
        stage = (payload or {}).get("stage")
        if not stage:
            raise ValidationError({"stage": "This field is required."})
        valid_stages = {choice[0] for choice in Application.Stage.choices}
        if stage not in valid_stages:
            raise ValidationError(
                {"stage": f"Invalid stage. Must be one of: {', '.join(sorted(valid_stages))}"}
            )
        return {"stage": stage}

    def resolve_queryset(self, *, organization, selection, user):
        return get_applications_bulk_queryset(organization=organization, selection=selection)

    def execute(self, *, job, queryset):
        stage = job.action_payload["stage"]
        batch_size = getattr(settings, "BULK_ACTION_BATCH_SIZE", 500)
        total = job.total_count
        updated_count = 0
        now = timezone.now()

        application_ids = list(queryset.values_list("pk", flat=True))
        for offset in range(0, len(application_ids), batch_size):
            batch_ids = application_ids[offset : offset + batch_size]
            with transaction.atomic():
                updated_count += Application.objects.filter(pk__in=batch_ids).update(
                    stage=stage,
                    updated_at=now,
                )

            processed = min(offset + len(batch_ids), total)
            progress = int((processed / total) * 100) if total else 100
            job.processed_count = processed
            job.progress = progress
            job.save(update_fields=["processed_count", "progress", "updated_at"])

        return {"updated_count": updated_count, "stage": stage}
