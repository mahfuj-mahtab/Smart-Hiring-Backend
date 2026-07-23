import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.jobs.models import Application, Job
from apps.organizations.services import OrganizationService


@pytest.mark.django_db
def test_public_jobs_list_only_open(api_client, organization, owner_user, job, open_job):
    api_client.credentials(HTTP_X_ORGANIZATION_SLUG=organization.slug)
    response = api_client.get("/api/v1/public/jobs/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == open_job.title


@pytest.mark.django_db
def test_public_jobs_requires_org(api_client):
    response = api_client.get("/api/v1/public/jobs/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_public_job_detail(api_client, organization, open_job):
    api_client.credentials(HTTP_X_ORGANIZATION_SLUG=organization.slug)
    response = api_client.get(f"/api/v1/public/jobs/{open_job.id}/")
    assert response.status_code == 200
    assert response.json()["data"]["title"] == open_job.title


@pytest.mark.django_db
def test_candidate_apply_success(candidate_client, open_job):
    cv = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 resume", content_type="application/pdf")
    response = candidate_client.post(
        "/api/v1/applications/",
        {"job": str(open_job.id), "cover_letter": "I am interested", "cv": cv},
        format="multipart",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert Application.objects.filter(job=open_job).count() == 1


@pytest.mark.django_db
def test_candidate_apply_duplicate_blocked(candidate_client, open_job, application):
    cv = SimpleUploadedFile("resume2.pdf", b"%PDF-1.4 resume", content_type="application/pdf")
    response = candidate_client.post(
        "/api/v1/applications/",
        {"job": str(open_job.id), "cv": cv},
        format="multipart",
    )
    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_candidate_apply_closed_job_blocked(candidate_client, job):
    cv = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 resume", content_type="application/pdf")
    response = candidate_client.post(
        "/api/v1/applications/",
        {"job": str(job.id), "cv": cv},
        format="multipart",
    )
    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_employer_list_applications(auth_client, application):
    response = auth_client.get("/api/v1/applications/")
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1


@pytest.mark.django_db
def test_employer_retrieve_application(auth_client, application):
    response = auth_client.get(f"/api/v1/applications/{application.id}/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(application.id)
    assert data["is_shortlisted"] is False
    assert "cover_letter" in data


@pytest.mark.django_db
def test_employer_toggle_shortlist(auth_client, application):
    response = auth_client.patch(
        f"/api/v1/applications/{application.id}/",
        {"is_shortlisted": True},
        format="json",
    )
    assert response.status_code == 200
    application.refresh_from_db()
    assert application.is_shortlisted is True
    assert response.json()["data"]["is_shortlisted"] is True


@pytest.mark.django_db
def test_employer_application_neighbors(auth_client, application, open_job, organization):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.accounts.services import CandidateService
    from apps.jobs.models import Application

    other_candidate, _ = CandidateService.register_candidate(
        email="other@example.com",
        username="othercandidate",
        password="testpass123",
        first_name="Other",
        last_name="Candidate",
    )
    cv = SimpleUploadedFile("resume2.pdf", b"%PDF-1.4 resume content", content_type="application/pdf")
    Application.objects.create(
        organization=organization,
        job=open_job,
        candidate=other_candidate,
        stage=Application.Stage.SCREENING,
        cv=cv,
        created_by=other_candidate,
    )

    response = auth_client.get(f"/api/v1/applications/{application.id}/neighbors/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 2
    assert data["position"] >= 1

@pytest.mark.django_db
def test_employer_update_application_stage(auth_client, application):
    response = auth_client.patch(
        f"/api/v1/applications/{application.id}/",
        {"stage": "interview"},
        format="json",
    )
    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == Application.Stage.INTERVIEW


@pytest.mark.django_db
def test_candidate_cannot_list_employer_applications(candidate_client, application):
    response = candidate_client.get("/api/v1/applications/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_candidate_applications_me(candidate_client, application):
    response = candidate_client.get("/api/v1/applications/me/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["job_title"] == application.job.title
