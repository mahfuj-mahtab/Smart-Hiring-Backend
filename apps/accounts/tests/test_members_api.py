import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import OrganizationMember, Role
from apps.accounts.services import UserService

User = get_user_model()


@pytest.mark.django_db
def test_lookup_user_found(auth_client, organization, member_user):
    response = auth_client.get(
        "/api/v1/members/lookup-user/",
        {"email": member_user.email},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "found"
    assert data["user"]["email"] == member_user.email


@pytest.mark.django_db
def test_lookup_user_not_found(auth_client):
    response = auth_client.get(
        "/api/v1/members/lookup-user/",
        {"email": "nobody@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "not_found"


@pytest.mark.django_db
def test_lookup_user_already_member(auth_client, organization, owner_user):
    response = auth_client.get(
        "/api/v1/members/lookup-user/",
        {"email": owner_user.email},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "already_member"


@pytest.mark.django_db
def test_lookup_user_candidate_account(auth_client, candidate_user):
    response = auth_client.get(
        "/api/v1/members/lookup-user/",
        {"email": candidate_user.email},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "invalid_account"


@pytest.mark.django_db
def test_lookup_user_requires_owner(member_client):
    response = member_client.get(
        "/api/v1/members/lookup-user/",
        {"email": "someone@example.com"},
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_member_with_existing_user(auth_client, organization, member_user, hr_role):
    response = auth_client.post(
        "/api/v1/members/",
        {
            "user": str(member_user.id),
            "role": str(hr_role.id),
            "is_active": True,
        },
        format="json",
    )
    assert response.status_code == 201
    assert OrganizationMember.objects.filter(
        organization=organization,
        user=member_user,
    ).exists()


@pytest.mark.django_db
def test_create_member_with_new_user(auth_client, organization, hr_role):
    response = auth_client.post(
        "/api/v1/members/",
        {
            "new_user": {
                "email": "newhire@example.com",
                "username": "newhire",
                "password": "testpass123",
                "first_name": "New",
                "last_name": "Hire",
            },
            "role": str(hr_role.id),
            "is_active": True,
        },
        format="json",
    )
    assert response.status_code == 201
    user = User.objects.get(email="newhire@example.com")
    assert user.account_type == User.AccountType.EMPLOYER
    assert OrganizationMember.objects.filter(organization=organization, user=user).exists()


@pytest.mark.django_db
def test_create_member_rejects_both_user_and_new_user(auth_client, member_user, hr_role):
    response = auth_client.post(
        "/api/v1/members/",
        {
            "user": str(member_user.id),
            "new_user": {
                "email": "other@example.com",
                "username": "other",
                "password": "testpass123",
            },
            "role": str(hr_role.id),
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_member_duplicate_email_in_new_user(auth_client, hr_role, member_user):
    response = auth_client.post(
        "/api/v1/members/",
        {
            "new_user": {
                "email": member_user.email,
                "username": "duplicate",
                "password": "testpass123",
            },
            "role": str(hr_role.id),
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_employer_user_service():
    user = UserService.create_employer_user(
        email="service@example.com",
        username="serviceuser",
        password="testpass123",
        first_name="Service",
        last_name="User",
    )
    assert user.account_type == User.AccountType.EMPLOYER
    assert user.email == "service@example.com"
