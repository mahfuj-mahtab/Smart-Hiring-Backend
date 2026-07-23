from django_filters import rest_framework as filters

from apps.common.filters import BaseFilterSet
from apps.accounts.models import OrganizationMember, Role


class RoleFilter(BaseFilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    is_system = filters.BooleanFilter()

    class Meta:
        model = Role
        fields = ["name", "is_system"]


class OrganizationMemberFilter(BaseFilterSet):
    is_active = filters.BooleanFilter()
    role = filters.UUIDFilter(field_name="role_id")
    email = filters.CharFilter(field_name="user__email", lookup_expr="icontains")

    class Meta:
        model = OrganizationMember
        fields = ["is_active", "role", "email"]
