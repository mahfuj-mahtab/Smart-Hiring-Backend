import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.common.bulk_actions.services import BulkActionService
from apps.common.models import BulkAuditLog, BulkJob
from apps.jobs.models import Application


@pytest.fixture(autouse=True)
def celery_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


def _start_bulk(auth_client, payload, idempotency_key=None):
    headers = {}
    if idempotency_key:
        headers["HTTP_IDEMPOTENCY_KEY"] = idempotency_key
    return auth_client.post(
        "/api/v1/bulk-actions/",
        payload,
        format="json",
        **headers,
    )


@pytest.mark.django_db
def test_bulk_change_stage_by_ids(auth_client, application):
    response = _start_bulk(
        auth_client,
        {
            "resource": "applications",
            "action": "change_stage",
            "selection": {"mode": "ids", "ids": [str(application.id)]},
            "payload": {"stage": "interview"},
        },
    )
    assert response.status_code == 202
    job_id = response.json()["data"]["id"]
    job = BulkJob.objects.get(pk=job_id)
    assert job.status == BulkJob.Status.COMPLETED
    assert job.progress == 100
    application.refresh_from_db()
    assert application.stage == Application.Stage.INTERVIEW
    assert BulkAuditLog.objects.filter(bulk_job=job).count() == 1


@pytest.mark.django_db
def test_bulk_change_stage_by_filter(auth_client, application, open_job):
    response = _start_bulk(
        auth_client,
        {
            "resource": "applications",
            "action": "change_stage",
            "selection": {
                "mode": "filter",
                "filters": {"stage": "applied", "job": str(open_job.id)},
            },
            "payload": {"stage": "screening"},
        },
    )
    assert response.status_code == 202
    application.refresh_from_db()
    assert application.stage == Application.Stage.SCREENING


@pytest.mark.django_db
def test_bulk_change_stage_invalid_action(auth_client, application):
    response = _start_bulk(
        auth_client,
        {
            "resource": "applications",
            "action": "invalid_action",
            "selection": {"mode": "ids", "ids": [str(application.id)]},
            "payload": {"stage": "interview"},
        },
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_bulk_change_stage_permission_denied(member_client, application, hr_member):
    response = _start_bulk(
        member_client,
        {
            "resource": "applications",
            "action": "change_stage",
            "selection": {"mode": "ids", "ids": [str(application.id)]},
            "payload": {"stage": "interview"},
        },
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_bulk_idempotency(auth_client, application):
    key = str(uuid.uuid4())
    payload = {
        "resource": "applications",
        "action": "change_stage",
        "selection": {"mode": "ids", "ids": [str(application.id)]},
        "payload": {"stage": "offer"},
    }
    first = _start_bulk(auth_client, payload, idempotency_key=key)
    second = _start_bulk(auth_client, payload, idempotency_key=key)
    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert BulkJob.objects.filter(idempotency_key=key).count() == 1


@pytest.mark.django_db
def test_bulk_export_download(auth_client, application):
    start = _start_bulk(
        auth_client,
        {
            "resource": "applications",
            "action": "export",
            "selection": {"mode": "ids", "ids": [str(application.id)]},
            "payload": {},
        },
    )
    assert start.status_code == 202
    job_id = start.json()["data"]["id"]
    job = BulkJob.objects.get(pk=job_id)
    assert job.status == BulkJob.Status.COMPLETED
    assert job.result.get("download_path")

    download = auth_client.get(f"/api/v1/bulk-actions/{job_id}/download/")
    assert download.status_code == 200
    assert (
        download["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@pytest.mark.django_db
def test_bulk_org_isolation(auth_client, application, owner_user):
    from apps.organizations.services import OrganizationService

    other_org = OrganizationService.create_organization(
        name="Other Org",
        slug="otherorg",
        owner=owner_user,
    )
    other_job_org_application_id = application.id

    response = _start_bulk(
        auth_client,
        {
            "resource": "applications",
            "action": "change_stage",
            "selection": {"mode": "ids", "ids": [str(other_job_org_application_id)]},
            "payload": {"stage": "rejected"},
        },
    )
    assert response.status_code == 202
    application.refresh_from_db()
    assert application.stage == Application.Stage.REJECTED

    cv = SimpleUploadedFile("resume2.pdf", b"%PDF-1.4 resume", content_type="application/pdf")
    from apps.jobs.models import Job

    foreign_job = Job.objects.create(
        organization=other_org,
        title="Foreign",
        description="Foreign job",
        status=Job.Status.OPEN,
        created_by=owner_user,
    )
    from apps.accounts.services import CandidateService

    candidate, _ = CandidateService.register_candidate(
        email="foreign@example.com",
        username="foreigncandidate",
        password="testpass123",
    )
    foreign_app = Application.objects.create(
        organization=other_org,
        job=foreign_job,
        candidate=candidate,
        stage=Application.Stage.APPLIED,
        cv=cv,
    )

    response = _start_bulk(
        auth_client,
        {
            "resource": "applications",
            "action": "change_stage",
            "selection": {"mode": "ids", "ids": [str(foreign_app.id)]},
            "payload": {"stage": "rejected"},
        },
    )
    assert response.status_code == 400
    foreign_app.refresh_from_db()
    assert foreign_app.stage == Application.Stage.APPLIED


@pytest.mark.django_db
def test_bulk_job_retrieve_progress(auth_client, application):
    response = _start_bulk(
        auth_client,
        {
            "resource": "applications",
            "action": "change_stage",
            "selection": {"mode": "ids", "ids": [str(application.id)]},
            "payload": {"stage": "hired"},
        },
    )
    job_id = response.json()["data"]["id"]
    detail = auth_client.get(f"/api/v1/bulk-actions/{job_id}/")
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["status"] == BulkJob.Status.COMPLETED
    assert data["progress"] == 100


@pytest.mark.django_db
def test_bulk_run_job_directly(application, organization, owner_user):
    job = BulkJob.objects.create(
        organization=organization,
        created_by=owner_user,
        resource="applications",
        action="change_stage",
        selection_mode="ids",
        selection_data={"mode": "ids", "ids": [str(application.id)]},
        action_payload={"stage": "offer"},
        total_count=1,
    )
    BulkActionService.run_job(str(job.id))
    job.refresh_from_db()
    assert job.status == BulkJob.Status.COMPLETED
    application.refresh_from_db()
    assert application.stage == Application.Stage.OFFER
