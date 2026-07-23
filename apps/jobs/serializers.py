from rest_framework import serializers

from apps.common.serializers import BaseModelSerializer
from apps.jobs.models import Application, Job

JOB_FIELDS = [
    "id",
    "title",
    "description",
    "department",
    "location",
    "employment_type",
    "work_mode",
    "experience_level",
    "salary_min",
    "salary_max",
    "salary_currency",
    "requirements",
    "responsibilities",
    "benefits",
    "application_deadline",
    "vacancies",
    "status",
    "created_at",
    "updated_at",
]

JOB_WRITE_FIELDS = [
    "title",
    "description",
    "department",
    "location",
    "employment_type",
    "work_mode",
    "experience_level",
    "salary_min",
    "salary_max",
    "salary_currency",
    "requirements",
    "responsibilities",
    "benefits",
    "application_deadline",
    "vacancies",
    "status",
]


class JobListSerializer(serializers.ModelSerializer):
    application_count = serializers.IntegerField(source="applications.count", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "department",
            "location",
            "employment_type",
            "work_mode",
            "experience_level",
            "salary_min",
            "salary_max",
            "salary_currency",
            "vacancies",
            "status",
            "application_count",
            "application_deadline",
            "created_at",
            "updated_at",
        ]


class JobDetailSerializer(BaseModelSerializer):
    application_count = serializers.IntegerField(source="applications.count", read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Job
        fields = JOB_FIELDS + [
            "application_count",
            "organization",
            "created_by",
        ]


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = JOB_WRITE_FIELDS

    def validate_status(self, value):
        if value not in (Job.Status.DRAFT, Job.Status.OPEN):
            raise serializers.ValidationError("New jobs can only be created as draft or open.")
        return value

    def validate(self, attrs):
        salary_min = attrs.get("salary_min")
        salary_max = attrs.get("salary_max")
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError({"salary_max": "Maximum salary must be greater than minimum."})
        return attrs


class JobUpdateSerializer(JobCreateSerializer):
    pass


class PublicJobListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "department",
            "location",
            "employment_type",
            "work_mode",
            "experience_level",
            "salary_min",
            "salary_max",
            "salary_currency",
            "vacancies",
            "application_deadline",
            "organization_name",
            "organization_slug",
            "created_at",
        ]


class PublicJobDetailSerializer(PublicJobListSerializer):
    class Meta(PublicJobListSerializer.Meta):
        fields = PublicJobListSerializer.Meta.fields + [
            "description",
            "requirements",
            "responsibilities",
            "benefits",
        ]


class ApplicationListSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.EmailField(source="candidate.email", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    cv_url = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "job_title",
            "candidate",
            "candidate_name",
            "candidate_email",
            "phone",
            "linkedin_url",
            "portfolio_url",
            "years_of_experience",
            "cv_url",
            "stage",
            "is_shortlisted",
            "applied_at",
            "created_at",
            "updated_at",
        ]

    def get_candidate_name(self, obj):
        return obj.candidate.get_full_name() or obj.candidate.username

    def get_cv_url(self, obj):
        if not obj.cv:
            return None
        from django.conf import settings

        return f"{settings.PUBLIC_API_URL}{obj.cv.url}"


class ApplicationDetailSerializer(ApplicationListSerializer):
    cover_letter = serializers.CharField(read_only=True)

    class Meta(ApplicationListSerializer.Meta):
        fields = ApplicationListSerializer.Meta.fields + ["cover_letter"]


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            "job",
            "cover_letter",
            "phone",
            "linkedin_url",
            "portfolio_url",
            "years_of_experience",
            "cv",
        ]

    def validate_job(self, value):
        organization = self.context["request"].organization
        if organization is None:
            raise serializers.ValidationError("Organization context is required.")
        if value.organization_id != organization.id:
            raise serializers.ValidationError("Job does not belong to this organization.")
        return value

    def validate_cv(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("CV file must be 5MB or smaller.")
        return value


class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["stage", "is_shortlisted"]

    def validate_stage(self, value):
        valid = {choice[0] for choice in Application.Stage.choices}
        if value not in valid:
            raise serializers.ValidationError(f"Invalid stage. Must be one of: {', '.join(sorted(valid))}")
        return value


class CandidateApplicationSerializer(ApplicationListSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta(ApplicationListSerializer.Meta):
        fields = ApplicationListSerializer.Meta.fields + ["organization_name"]
