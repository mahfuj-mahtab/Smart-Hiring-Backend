import pytest

from apps.accounts.models import Permission, Role


@pytest.mark.django_db
def test_list_roles_success(auth_client, organization):
    response = auth_client.get("/api/v1/roles/")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]) >= 1


@pytest.mark.django_db
def test_create_role_success(auth_client, organization):
    perm = Permission.objects.get(codename="job.view")
    response = auth_client.post(
        "/api/v1/roles/",
        {"name": "Recruiter", "permission_ids": [str(perm.id)]},
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Recruiter"
    assert Role.objects.filter(organization=organization, name="Recruiter").exists()


@pytest.mark.django_db
def test_create_role_forbidden_for_member_without_permission(member_client, hr_member):
    response = member_client.post(
        "/api/v1/roles/",
        {"name": "Blocked"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_role_validation_duplicate_name(auth_client, organization):
    Role.objects.create(organization=organization, name="Duplicate")
    response = auth_client.post(
        "/api/v1/roles/",
        {"name": "Duplicate"},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["success"] is False
