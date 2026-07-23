import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import OrganizationMember, Role
from apps.organizations.services import OrganizationService

User = get_user_model()


@pytest.mark.django_db
def test_user_cannot_access_other_org_data(api_client, owner_user):
    org_a = OrganizationService.create_organization(
        name="Org A",
        slug="orga",
        owner=owner_user,
    )
    other_owner = User.objects.create_user(
        username="other",
        email="other@example.com",
        password="testpass123",
    )
    org_b = OrganizationService.create_organization(
        name="Org B",
        slug="orgb",
        owner=other_owner,
    )

    api_client.force_authenticate(user=owner_user)
    api_client.credentials(HTTP_X_ORGANIZATION_SLUG=org_b.slug)

    response = api_client.get("/api/v1/roles/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_roles_scoped_to_current_org(auth_client, organization, owner_user):
    other_owner = User.objects.create_user(
        username="other2",
        email="other2@example.com",
        password="testpass123",
    )
    org_b = OrganizationService.create_organization(
        name="Org B2",
        slug="orgb2",
        owner=other_owner,
    )
    Role.objects.create(organization=org_b, name="External Role")

    response = auth_client.get("/api/v1/roles/")
    role_names = [role["name"] for role in response.json()["data"]]
    assert "External Role" not in role_names
    assert "Owner" in role_names
