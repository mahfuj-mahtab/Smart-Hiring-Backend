import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.accounts.models import Permission, Role


def make_image(name="logo.png", size=1024):
    buf = io.BytesIO()
    dimension = max(10, int(size**0.5))
    img = Image.new("RGB", (dimension, dimension), color="red")
    img.save(buf, format="PNG")
    content = buf.getvalue()
    if len(content) < size:
        content += b"\x00" * (size - len(content))
    return SimpleUploadedFile(name, content, content_type="image/png")


@pytest.mark.django_db
def test_get_organization_success(auth_client, organization):
    response = auth_client.get("/api/v1/organization/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == organization.name
    assert body["data"]["slug"] == organization.slug


@pytest.mark.django_db
def test_patch_organization_success(auth_client, organization):
    response = auth_client.patch(
        "/api/v1/organization/",
        {
            "name": "Updated Org",
            "industry": "Technology",
            "employee_size": "11-50",
        },
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Updated Org"
    assert body["data"]["industry"] == "Technology"
    assert body["data"]["employee_size"] == "11-50"

    organization.refresh_from_db()
    assert organization.name == "Updated Org"


@pytest.mark.django_db
def test_patch_organization_with_logo(auth_client, organization):
    logo = make_image()
    response = auth_client.patch(
        "/api/v1/organization/",
        {"logo": logo},
        format="multipart",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["logo"] is not None

    organization.refresh_from_db()
    assert organization.logo


@pytest.mark.django_db
def test_patch_organization_forbidden_without_permission(member_client, hr_member):
    response = member_client.patch(
        "/api/v1/organization/",
        {"name": "Blocked"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_patch_organization_allowed_with_change_permission(
    member_client, organization, hr_member
):
    change_perm = Permission.objects.get(codename="organization.change")
    view_perm = Permission.objects.get(codename="organization.view")
    role = Role.objects.create(organization=organization, name="Org Admin")
    role.permissions.set([change_perm, view_perm])
    hr_member.role = role
    hr_member.save()

    response = member_client.patch(
        "/api/v1/organization/",
        {"industry": "Finance"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["data"]["industry"] == "Finance"


@pytest.mark.django_db
def test_patch_organization_invalid_logo_size(auth_client, organization):
    logo = make_image(size=3 * 1024 * 1024)
    response = auth_client.patch(
        "/api/v1/organization/",
        {"logo": logo},
        format="multipart",
    )
    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_public_organization_success(api_client, organization):
    api_client.credentials(HTTP_X_ORGANIZATION_SLUG=organization.slug)
    response = api_client.get("/api/v1/public/organization/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == organization.name
    assert body["data"]["slug"] == organization.slug


@pytest.mark.django_db
def test_public_organization_not_found_without_context(api_client):
    response = api_client.get("/api/v1/public/organization/")
    assert response.status_code == 404
