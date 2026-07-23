from collections import defaultdict

from apps.jobs.models import Application, Job


def get_open_jobs(organization):
    return Job.objects.filter(
        organization=organization,
        status=Job.Status.OPEN,
    ).select_related("organization")


def get_applications_for_org(organization):
    return Application.objects.filter(
        organization=organization,
    ).select_related(
        "job",
        "candidate",
        "candidate__candidate_profile",
    )


def get_applications_grouped_by_stage(organization, job_id=None):
    qs = get_applications_for_org(organization)
    if job_id:
        qs = qs.filter(job_id=job_id)

    grouped = defaultdict(list)
    for application in qs:
        grouped[application.stage].append(application)
    return dict(grouped)


def get_application_neighbors(*, queryset, application_id):
    application_ids = list(queryset.values_list("pk", flat=True))
    try:
        index = application_ids.index(application_id)
    except ValueError:
        return {
            "previous_id": None,
            "next_id": None,
            "position": 0,
            "total": len(application_ids),
        }

    return {
        "previous_id": application_ids[index - 1] if index > 0 else None,
        "next_id": application_ids[index + 1] if index < len(application_ids) - 1 else None,
        "position": index + 1,
        "total": len(application_ids),
    }
