import pytest
from rest_framework.exceptions import ValidationError

from apps.jobs.models import Job
from apps.subscriptions.services import SubscriptionService


@pytest.mark.django_db
def test_job_under_limit_allowed(organization, owner_user):
    Job.objects.create(
        organization=organization,
        title="Job 1",
        description="Desc",
        created_by=owner_user,
    )
    SubscriptionService.check_limit(organization, "jobs")


@pytest.mark.django_db
def test_job_at_limit_blocked(organization, owner_user):
    organization.subscription.plan.max_jobs = 1
    organization.subscription.plan.save()
    Job.objects.create(
        organization=organization,
        title="Job 1",
        description="Desc",
        created_by=owner_user,
    )

    with pytest.raises(ValidationError) as exc_info:
        SubscriptionService.check_limit(organization, "jobs")
    assert "Plan limit reached" in str(exc_info.value)


@pytest.mark.django_db
def test_create_job_at_limit_blocked(auth_client, organization, owner_user):
    organization.subscription.plan.max_jobs = 1
    organization.subscription.plan.save()
    Job.objects.create(
        organization=organization,
        title="Existing Job",
        description="Desc",
        created_by=owner_user,
    )

    response = auth_client.post(
        "/api/v1/jobs/",
        {"title": "New Job", "description": "Another role"},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["success"] is False
