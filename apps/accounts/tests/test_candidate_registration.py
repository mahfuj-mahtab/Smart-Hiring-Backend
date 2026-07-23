import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import CandidateProfile, User
from apps.organizations.models import Organization

UserModel = get_user_model()


@pytest.fixture
def candidate_user(db):
    user = UserModel.objects.create_user(
        username="candidate1",
        email="candidate1@example.com",
        password="testpass123",
        account_type=User.AccountType.CANDIDATE,
    )
    CandidateProfile.objects.create(user=user, phone="+8801700000000")
    return user


@pytest.fixture
def candidate_client(api_client, candidate_user):
    api_client.force_authenticate(user=candidate_user)
    return api_client


@pytest.mark.django_db
def test_candidate_register_creates_user_without_org(api_client):
    response = api_client.post(
        "/api/v1/auth/register/candidate/",
        {
            "email": "newcandidate@example.com",
            "username": "newcandidate",
            "password": "testpass123",
            "first_name": "New",
            "last_name": "Candidate",
            "phone": "+8801700000001",
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user"]["account_type"] == User.AccountType.CANDIDATE
    assert "organization" not in body["data"]
    assert Organization.objects.count() == 0

    user = UserModel.objects.get(email="newcandidate@example.com")
    assert user.account_type == User.AccountType.CANDIDATE
    assert hasattr(user, "candidate_profile")
    assert user.candidate_profile.phone == "+8801700000001"


@pytest.mark.django_db
def test_employer_register_still_creates_org(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "employer@example.com",
            "username": "employer",
            "password": "testpass123",
            "organization_name": "Acme Corp",
            "organization_slug": "acme",
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["user"]["account_type"] == User.AccountType.EMPLOYER
    assert body["data"]["organization"]["slug"] == "acme"
    assert Organization.objects.filter(slug="acme").exists()


@pytest.mark.django_db
def test_candidate_cannot_access_employer_roles(candidate_client, organization):
    candidate_client.credentials(HTTP_X_ORGANIZATION_SLUG=organization.slug)
    response = candidate_client.get("/api/v1/roles/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_employer_cannot_access_candidate_me(auth_client):
    response = auth_client.get("/api/v1/candidate/me/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_candidate_me_endpoint(candidate_client):
    response = candidate_client.get("/api/v1/candidate/me/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "candidate1@example.com"
    assert body["data"]["account_type"] == User.AccountType.CANDIDATE
    assert body["data"]["phone"] == "+8801700000000"


@pytest.mark.django_db
def test_candidate_cannot_register_as_employer_with_same_email(api_client):
    api_client.post(
        "/api/v1/auth/register/candidate/",
        {
            "email": "shared@example.com",
            "username": "sharedcandidate",
            "password": "testpass123",
        },
        format="json",
    )

    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "shared@example.com",
            "username": "sharedemployer",
            "password": "testpass123",
            "organization_name": "Shared Org",
            "organization_slug": "shared",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "candidate account" in str(response.json()).lower()


@pytest.mark.django_db
def test_employer_cannot_register_as_candidate_with_same_email(api_client):
    api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "employeronly@example.com",
            "username": "employeronly",
            "password": "testpass123",
            "organization_name": "Employer Org",
            "organization_slug": "employeronly",
        },
        format="json",
    )

    response = api_client.post(
        "/api/v1/auth/register/candidate/",
        {
            "email": "employeronly@example.com",
            "username": "candidateattempt",
            "password": "testpass123",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "employer account" in str(response.json()).lower()
