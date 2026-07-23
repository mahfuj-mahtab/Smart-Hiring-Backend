import json

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.common.middleware import SubdomainOrganizationMiddleware
from apps.organizations.models import Organization
from apps.organizations.services import OrganizationService

User = get_user_model()


@pytest.fixture
def rf():
    return RequestFactory()


def _process_request(rf, host, path="/api/v1/roles/", header_slug=None):
    middleware = SubdomainOrganizationMiddleware(lambda request: request)
    headers = {}
    if header_slug:
        headers["HTTP_X_ORGANIZATION_SLUG"] = header_slug
    request = rf.get(path, **headers)
    request.META["HTTP_HOST"] = host
    return middleware(request)


@pytest.mark.django_db
def test_middleware_resolves_org_from_header(rf, owner_user):
    org = OrganizationService.create_organization(
        name="Acme",
        slug="acme",
        owner=owner_user,
    )
    request = _process_request(rf, "localhost", header_slug="acme")
    assert request.organization == org


@pytest.mark.django_db
def test_middleware_invalid_slug_returns_404(rf):
    response = _process_request(rf, "localhost", header_slug="missing")
    assert response.status_code == 404
    payload = json.loads(response.content)
    assert payload["success"] is False


@pytest.mark.django_db
def test_middleware_exempt_auth_paths(rf):
    middleware = SubdomainOrganizationMiddleware(lambda request: request)
    request = rf.post("/api/v1/auth/register/")
    request.META["HTTP_HOST"] = "localhost"
    response = middleware(request)
    assert response.organization is None


@pytest.mark.django_db
def test_middleware_inactive_org_returns_404(rf, owner_user):
    org = OrganizationService.create_organization(
        name="Inactive",
        slug="inactive",
        owner=owner_user,
    )
    org.is_active = False
    org.save()
    response = _process_request(rf, "localhost", header_slug="inactive")
    assert response.status_code == 404
