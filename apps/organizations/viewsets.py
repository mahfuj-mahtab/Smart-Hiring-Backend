from rest_framework import mixins, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.accounts.permissions import HasPermission, IsEmployerUser
from apps.common.mixins import ActionSerializerMixin, ApiResponseMixin
from apps.common.permissions import IsOrganizationMember
from apps.common.responses import api_response
from apps.organizations.models import Organization
from apps.organizations.serializers import (
    OrganizationSerializer,
    OrganizationUpdateSerializer,
    PublicOrganizationSerializer,
)
from apps.organizations.services import OrganizationService


class OrganizationViewSet(
    ApiResponseMixin,
    ActionSerializerMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "patch", "head", "options"]
    serializer_action_classes = {
        "retrieve": OrganizationSerializer,
        "update": OrganizationUpdateSerializer,
        "partial_update": OrganizationUpdateSerializer,
    }

    def get_permissions(self):
        if self.action in ("update", "partial_update"):
            permission_class = HasPermission("organization.change")
        else:
            permission_class = HasPermission("organization.view")
        return [
            IsAuthenticated(),
            IsEmployerUser(),
            IsOrganizationMember(),
            permission_class(),
        ]

    def get_object(self):
        organization = self.request.organization
        if organization is None:
            raise ValidationError({"detail": "Organization context is required."})
        return organization

    def perform_update(self, serializer):
        organization = OrganizationService.update_organization(
            organization=serializer.instance,
            data=serializer.validated_data,
        )
        serializer.instance = organization

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        detail = OrganizationSerializer(instance, context={"request": request})
        return api_response(True, "Updated successfully", data=detail.data)


class PublicOrganizationViewSet(
    ApiResponseMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]
    queryset = Organization.objects.all()
    serializer_class = PublicOrganizationSerializer
    http_method_names = ["get", "head", "options"]

    def get_object(self):
        organization = self.request.organization
        if organization is None:
            raise NotFound("Organization context is required.")
        return organization
