from django_filters import rest_framework as filters

from apps.common.filters import BaseFilterSet
from apps.jobs.models import Application, Job


class JobFilter(BaseFilterSet):
    status = filters.ChoiceFilter(choices=Job.Status.choices)
    employment_type = filters.ChoiceFilter(choices=Job.EmploymentType.choices)
    work_mode = filters.ChoiceFilter(choices=Job.WorkMode.choices)
    experience_level = filters.ChoiceFilter(choices=Job.ExperienceLevel.choices)
    department = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Job
        fields = ["status", "employment_type", "work_mode", "experience_level", "department"]


class ApplicationFilter(BaseFilterSet):
    stage = filters.ChoiceFilter(choices=Application.Stage.choices)
    job = filters.UUIDFilter(field_name="job_id")
    is_shortlisted = filters.BooleanFilter()

    class Meta:
        model = Application
        fields = ["stage", "job", "is_shortlisted"]
