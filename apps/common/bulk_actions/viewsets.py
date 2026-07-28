import os

from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import HasPermission, IsEmployerUser
from apps.common.models import BulkJob
from apps.common.bulk_actions.serializers import BulkActionCreateSerializer, BulkJobSerializer
from apps.common.bulk_actions.services import BulkActionService
from apps.common.permissions import IsOrganizationMember
from apps.common.responses import api_response


class BulkActionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsEmployerUser, IsOrganizationMember]
    serializer_class = BulkJobSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [
                IsAuthenticated(),
                IsEmployerUser(),
                IsOrganizationMember(),
            ]
        return [
            IsAuthenticated(),
            IsEmployerUser(),
            IsOrganizationMember(),
            HasPermission("candidate.view")(),
        ]

    def get_queryset(self):
        organization = getattr(self.request, "organization", None)
        if organization is None:
            return BulkJob.objects.none()
        return BulkJob.objects.filter(organization=organization)

    def create(self, request, *args, **kwargs):
        if request.organization is None:
            raise ValidationError({"detail": "Organization context is required."})

        serializer = BulkActionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idempotency_key = (
            request.headers.get("Idempotency-Key")
            or serializer.validated_data.get("idempotency_key")
            or None
        )
        if idempotency_key == "":
            idempotency_key = None

        job = BulkActionService.start(
            organization=request.organization,
            user=request.user,
            resource=serializer.validated_data["resource"],
            action=serializer.validated_data["action"],
            selection=serializer.validated_data["selection"],
            payload=serializer.validated_data.get("payload"),
            idempotency_key=idempotency_key,
        )

        output = BulkJobSerializer(job, context={"request": request})
        message = "Bulk action started" if job.status == BulkJob.Status.PENDING else "Bulk action retrieved"
        return api_response(True, message, data=output.data, status=202)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkJobSerializer(instance, context={"request": request})
        return api_response(True, "Success", data=serializer.data)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        job = self.get_object()
        if job.action != "export":
            raise ValidationError({"detail": "This job does not have a downloadable export."})
        if job.status != BulkJob.Status.COMPLETED:
            raise ValidationError({"detail": "Export is not ready yet."})

        download_path = job.result.get("download_path")
        if not download_path:
            raise NotFound("Export file not found.")

        from django.conf import settings

        file_path = os.path.join(settings.MEDIA_ROOT, download_path)
        if not os.path.isfile(file_path):
            raise NotFound("Export file not found.")

        filename = os.path.basename(file_path)
        response = FileResponse(
            open(file_path, "rb"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            filename=filename,
        )
        return response
