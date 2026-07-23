import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import OrganizationMember, Permission, Role
from apps.organizations.models import Organization
from apps.organizations.services import OrganizationService
from apps.subscriptions.models import Plan, Subscription

User = get_user_model()


@pytest.fixture(autouse=True)
def seed_permissions(db):
    call_command("seed_permissions")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner_user(db):
    return User.objects.create_user(
        username="owner",
        email="owner@example.com",
        password="testpass123",
    )


@pytest.fixture
def member_user(db):
    return User.objects.create_user(
        username="member",
        email="member@example.com",
        password="testpass123",
    )


@pytest.fixture
def organization(owner_user):
    return OrganizationService.create_organization(
        name="Test Org",
        slug="testorg",
        owner=owner_user,
    )


@pytest.fixture
def hr_role(organization):
    view_perm = Permission.objects.get(codename="role.view")
    role = Role.objects.create(organization=organization, name="HR")
    role.permissions.set([view_perm])
    return role


@pytest.fixture
def hr_member(organization, member_user, hr_role):
    return OrganizationMember.objects.create(
        organization=organization,
        user=member_user,
        role=hr_role,
        is_active=True,
    )


@pytest.fixture
def auth_client(api_client, owner_user, organization):
    api_client.force_authenticate(user=owner_user)
    api_client.credentials(HTTP_X_ORGANIZATION_SLUG=organization.slug)
    return api_client


@pytest.fixture
def member_client(api_client, member_user, organization):
    api_client.force_authenticate(user=member_user)
    api_client.credentials(HTTP_X_ORGANIZATION_SLUG=organization.slug)
    return api_client


@pytest.fixture
def free_plan(db):
    return Plan.objects.get(slug="free")


@pytest.fixture
def candidate_user(db):
    from apps.accounts.services import CandidateService

    user, _ = CandidateService.register_candidate(
        email="candidate@example.com",
        username="candidate",
        password="testpass123",
        first_name="Test",
        last_name="Candidate",
    )
    return user


@pytest.fixture
def candidate_client(api_client, candidate_user, organization):
    api_client.force_authenticate(user=candidate_user)
    api_client.credentials(HTTP_X_ORGANIZATION_SLUG=organization.slug)
    return api_client


@pytest.fixture
def job(organization, owner_user):
    from apps.jobs.models import Job

    return Job.objects.create(
        organization=organization,
        title="Software Engineer",
        description="Build great software",
        location="Remote",
        employment_type=Job.EmploymentType.FULL_TIME,
        work_mode=Job.WorkMode.REMOTE,
        status=Job.Status.DRAFT,
        created_by=owner_user,
    )


@pytest.fixture
def open_job(organization, owner_user):
    from apps.jobs.models import Job

    return Job.objects.create(
        organization=organization,
        title="Open Position",
        description="Join our team",
        location="NYC",
        employment_type=Job.EmploymentType.FULL_TIME,
        status=Job.Status.OPEN,
        created_by=owner_user,
    )


@pytest.fixture
def application(open_job, candidate_user, organization):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.jobs.models import Application

    cv = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 resume content", content_type="application/pdf")
    return Application.objects.create(
        organization=organization,
        job=open_job,
        candidate=candidate_user,
        stage=Application.Stage.APPLIED,
        cv=cv,
        created_by=candidate_user,
    )
