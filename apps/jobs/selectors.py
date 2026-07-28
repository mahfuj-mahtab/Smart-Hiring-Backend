from collections import defaultdict

from django.db.models import Q

from apps.jobs.filters import ApplicationFilter
from apps.jobs.models import Application, Job

APPLICATION_SEARCH_FIELDS = [
    "candidate__email",
    "candidate__username",
    "candidate__first_name",
    "candidate__last_name",
    "job__title",
    "phone",
]


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


def get_applications_bulk_queryset(*, organization, selection):
    qs = get_applications_for_org(organization)
    mode = selection.get("mode")

    if mode == "ids":
        ids = selection.get("ids") or []
        qs = qs.filter(id__in=ids)
        return qs

    if mode == "filter":
        filters = selection.get("filters") or {}
        filter_data = {
            key: value
            for key, value in filters.items()
            if key not in ("search", "ordering")
        }
        filterset = ApplicationFilter(filter_data, queryset=qs)
        qs = filterset.qs

        search = filters.get("search")
        if search:
            search_query = Q()
            for field in APPLICATION_SEARCH_FIELDS:
                search_query |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(search_query)

        ordering = filters.get("ordering") or "-applied_at"
        return qs.order_by(ordering)

    return qs.none()


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
