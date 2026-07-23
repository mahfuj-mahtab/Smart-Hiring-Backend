from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.accounts.filters import OrganizationMemberFilter, RoleFilter
from apps.accounts.models import OrganizationMember, Role
from apps.accounts.permissions import HasPermission, IsEmployerUser
from apps.accounts.selectors import lookup_employer_for_membership
from apps.accounts.serializers import (
    OrganizationMemberCreateSerializer,
    OrganizationMemberDetailSerializer,
    OrganizationMemberListSerializer,
    OrganizationMemberUpdateSerializer,
    RoleCreateSerializer,
    RoleDetailSerializer,
    RoleListSerializer,
)
from apps.accounts.services import MemberService, RoleService, UserService
from apps.common.permissions import IsOrganizationMember, IsOrganizationOwner
from apps.common.responses import api_response
from apps.common.viewsets import BaseModelViewSet


class RoleViewSet(BaseModelViewSet):
    queryset = Role.objects.prefetch_related("permissions")
    filterset_class = RoleFilter
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    serializer_class = RoleDetailSerializer
    serializer_action_classes = {
        "list": RoleListSerializer,
        "retrieve": RoleDetailSerializer,
        "create": RoleCreateSerializer,
        "update": RoleDetailSerializer,
        "partial_update": RoleDetailSerializer,
    }

    def get_permissions(self):
        permission_map = {
            "list": HasPermission("role.view"),
            "retrieve": HasPermission("role.view"),
            "create": HasPermission("role.add"),
            "update": HasPermission("role.change"),
            "partial_update": HasPermission("role.change"),
            "destroy": HasPermission("role.delete"),
        }
        permission_class = permission_map.get(self.action, HasPermission("role.view"))
        return [IsAuthenticated(), IsEmployerUser(), IsOrganizationMember(), permission_class()]

    def perform_create(self, serializer):
        permission_ids = serializer.validated_data.pop("permission_ids", [])
        role = RoleService.create_role(
            organization=self.request.organization,
            name=serializer.validated_data["name"],
            permission_ids=permission_ids,
        )
        serializer.instance = role

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = RoleDetailSerializer(serializer.instance)
        return api_response(True, "Created successfully", data=detail.data, status=201)

    def perform_update(self, serializer):
        permission_ids = serializer.validated_data.pop("permission_ids", None)
        name = serializer.validated_data.get("name")
        RoleService.update_role(
            role=serializer.instance,
            name=name,
            permission_ids=permission_ids,
        )
        serializer.instance.refresh_from_db()


class OrganizationMemberViewSet(BaseModelViewSet):
    queryset = OrganizationMember.objects.select_related("user", "role")
    filterset_class = OrganizationMemberFilter
    search_fields = ["user__email", "user__username", "user__first_name", "user__last_name"]
    ordering_fields = ["created_at", "user__email"]
    limit_resource = "members"
    serializer_class = OrganizationMemberDetailSerializer
    serializer_action_classes = {
        "list": OrganizationMemberListSerializer,
        "retrieve": OrganizationMemberDetailSerializer,
        "create": OrganizationMemberCreateSerializer,
        "update": OrganizationMemberUpdateSerializer,
        "partial_update": OrganizationMemberUpdateSerializer,
    }

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "lookup_user"):
            return [IsAuthenticated(), IsEmployerUser(), IsOrganizationMember(), IsOrganizationOwner()]
        return [IsAuthenticated(), IsEmployerUser(), IsOrganizationMember(), HasPermission("employee.view")()]

    def perform_create(self, serializer):
        organization = self.request.organization
        if self.limit_resource:
            from apps.subscriptions.services import SubscriptionService

            SubscriptionService.check_limit(organization, self.limit_resource)

        new_user_data = serializer.validated_data.pop("new_user", None)
        if new_user_data:
            user = UserService.create_employer_user(**new_user_data)
        else:
            user = serializer.validated_data["user"]

        member = MemberService.create_member(
            organization=organization,
            user=user,
            role=serializer.validated_data["role"],
            is_owner=False,
            created_by=self.request.user,
        )
        serializer.instance = member

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = OrganizationMemberDetailSerializer(serializer.instance)
        return api_response(True, "Created successfully", data=detail.data, status=201)

    def perform_update(self, serializer):
        MemberService.update_member(
            member=serializer.instance,
            role=serializer.validated_data.get("role"),
            is_active=serializer.validated_data.get("is_active"),
        )
        serializer.instance.refresh_from_db()

    def perform_destroy(self, instance):
        if instance.is_owner:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": "Cannot remove the organization owner."})
        instance.delete()

    @action(detail=False, methods=["get"], url_path="lookup-user")
    def lookup_user(self, request):
        email = request.query_params.get("email", "").strip()
        if not email:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"email": "Email is required."})
        data = lookup_employer_for_membership(organization=request.organization, email=email)
        return api_response(True, "Success", data=data)
