from django.db import transaction

from rest_framework.exceptions import ValidationError

from apps.jobs.models import Application, Job

JOB_WRITABLE_FIELDS = (
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
)


class JobService:
    @staticmethod
    @transaction.atomic
    def create_job(*, organization, created_by=None, **fields):
        payload = {key: fields[key] for key in JOB_WRITABLE_FIELDS if key in fields}
        return Job.objects.create(
            organization=organization,
            created_by=created_by,
            **payload,
        )

    @staticmethod
    @transaction.atomic
    def update_job(*, job, **fields):
        for key in JOB_WRITABLE_FIELDS:
            if key in fields and fields[key] is not None:
                setattr(job, key, fields[key])
        job.save()
        return job

    @staticmethod
    def publish_job(*, job):
        job.status = Job.Status.OPEN
        job.save(update_fields=["status", "updated_at"])
        return job

    @staticmethod
    def close_job(*, job):
        job.status = Job.Status.CLOSED
        job.save(update_fields=["status", "updated_at"])
        return job


class ApplicationService:
    @staticmethod
    @transaction.atomic
    def apply(*, organization, job, candidate, **fields):
        if job.organization_id != organization.id:
            raise ValidationError({"job": "Job does not belong to this organization."})
        if job.status != Job.Status.OPEN:
            raise ValidationError({"job": "This job is not accepting applications."})
        if candidate.account_type != "candidate":
            raise ValidationError({"candidate": "Only candidate accounts can apply to jobs."})
        if Application.objects.filter(job=job, candidate=candidate).exists():
            raise ValidationError({"detail": "You have already applied to this job."})

        cv = fields.get("cv")
        if not cv:
            raise ValidationError({"cv": "CV/resume is required."})

        return Application.objects.create(
            organization=organization,
            job=job,
            candidate=candidate,
            cover_letter=fields.get("cover_letter", ""),
            phone=fields.get("phone", ""),
            linkedin_url=fields.get("linkedin_url", ""),
            portfolio_url=fields.get("portfolio_url", ""),
            years_of_experience=fields.get("years_of_experience"),
            cv=cv,
            stage=Application.Stage.APPLIED,
            created_by=candidate,
        )

    @staticmethod
    @transaction.atomic
    def update_application(*, application, stage=None, is_shortlisted=None):
        update_fields = ["updated_at"]

        if stage is not None:
            valid_stages = {choice[0] for choice in Application.Stage.choices}
            if stage not in valid_stages:
                raise ValidationError(
                    {"stage": f"Invalid stage. Must be one of: {', '.join(sorted(valid_stages))}"}
                )
            application.stage = stage
            update_fields.append("stage")

        if is_shortlisted is not None:
            application.is_shortlisted = is_shortlisted
            update_fields.append("is_shortlisted")

        if len(update_fields) == 1:
            return application

        application.save(update_fields=update_fields)
        return application

    @staticmethod
    @transaction.atomic
    def update_stage(*, application, stage):
        return ApplicationService.update_application(application=application, stage=stage)
