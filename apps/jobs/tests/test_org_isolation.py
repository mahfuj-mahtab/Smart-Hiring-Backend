import pytest
from django.contrib.auth import get_user_model

from apps.jobs.models import Application, Job
from apps.organizations.services import OrganizationService

User = get_user_model()


@pytest.mark.django_db
def test_jobs_scoped_to_current_org(auth_client, organization, owner_user):
    other_owner = User.objects.create_user(
        username="otherjobs",
        email="otherjobs@example.com",
        password="testpass123",
    )
    org_b = OrganizationService.create_organization(
        name="Org Jobs B",
        slug="orgjobsb",
        owner=other_owner,
    )
    Job.objects.create(
        organization=org_b,
        title="External Job",
        description="Should not appear",
        created_by=other_owner,
    )
    Job.objects.create(
        organization=organization,
        title="Internal Job",
        description="Should appear",
        created_by=owner_user,
    )

    response = auth_client.get("/api/v1/jobs/")
    titles = [job["title"] for job in response.json()["data"]]
    assert "External Job" not in titles
    assert "Internal Job" in titles


@pytest.mark.django_db
def test_applications_scoped_to_current_org(auth_client, organization, owner_user, candidate_user):
    other_owner = User.objects.create_user(
        username="otherapps",
        email="otherapps@example.com",
        password="testpass123",
    )
    org_b = OrganizationService.create_organization(
        name="Org Apps B",
        slug="orgappsb",
        owner=other_owner,
    )
    job_b = Job.objects.create(
        organization=org_b,
        title="Other Job",
        description="Other",
        status=Job.Status.OPEN,
        created_by=other_owner,
    )
    Application.objects.create(
        organization=org_b,
        job=job_b,
        candidate=candidate_user,
        created_by=candidate_user,
    )

    job_a = Job.objects.create(
        organization=organization,
        title="Our Job",
        description="Ours",
        status=Job.Status.OPEN,
        created_by=owner_user,
    )
    Application.objects.create(
        organization=organization,
        job=job_a,
        candidate=candidate_user,
        created_by=candidate_user,
    )

    response = auth_client.get("/api/v1/applications/")
    job_titles = [app["job_title"] for app in response.json()["data"]]
    assert "Other Job" not in job_titles
    assert "Our Job" in job_titles
