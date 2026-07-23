import pytest

from apps.accounts.models import Permission, Role
from apps.accounts.permissions import HasPermission
from apps.accounts.selectors import user_has_permission
from apps.organizations.services import OrganizationService


@pytest.mark.django_db
def test_owner_has_all_permissions(owner_user, organization):
    assert user_has_permission(owner_user, organization, "job.add") is True
    assert user_has_permission(owner_user, organization, "role.delete") is True


@pytest.mark.django_db
def test_role_with_permission(owner_user, organization, member_user):
    perm = Permission.objects.get(codename="job.view")
    role = Role.objects.create(organization=organization, name="Viewer")
    role.permissions.add(perm)
    from apps.accounts.models import OrganizationMember

    OrganizationMember.objects.create(
        organization=organization,
        user=member_user,
        role=role,
    )
    assert user_has_permission(member_user, organization, "job.view") is True
    assert user_has_permission(member_user, organization, "job.add") is False


@pytest.mark.django_db
def test_has_permission_class_denies_without_membership(organization, member_user):
    from rest_framework.test import APIRequestFactory

    factory = APIRequestFactory()
    request = factory.get("/api/v1/roles/")
    request.user = member_user
    request.organization = organization

    permission = HasPermission("role.view")()
    assert permission.has_permission(request, view=None) is False
