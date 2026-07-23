import pytest

from apps.jobs.models import Job


@pytest.mark.django_db
def test_list_jobs_success(auth_client, job):
    response = auth_client.get("/api/v1/jobs/")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]) >= 1


@pytest.mark.django_db
def test_create_job_success(auth_client, organization):
    response = auth_client.post(
        "/api/v1/jobs/",
        {
            "title": "Backend Developer",
            "description": "Python/Django role",
            "location": "Remote",
            "employment_type": "full_time",
            "work_mode": "remote",
            "status": "draft",
        },
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Backend Developer"
    assert Job.objects.filter(organization=organization, title="Backend Developer").exists()


@pytest.mark.django_db
def test_create_job_forbidden_for_member_without_permission(member_client, hr_member):
    response = member_client.post(
        "/api/v1/jobs/",
        {"title": "Blocked", "description": "No access"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_update_job_success(auth_client, job):
    response = auth_client.patch(
        f"/api/v1/jobs/{job.id}/",
        {"status": "open"},
        format="json",
    )
    assert response.status_code == 200
    job.refresh_from_db()
    assert job.status == Job.Status.OPEN


@pytest.mark.django_db
def test_delete_job_success(auth_client, job):
    response = auth_client.delete(f"/api/v1/jobs/{job.id}/")
    assert response.status_code == 204
    assert not Job.objects.filter(id=job.id).exists()
