import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import BaseModel


def application_cv_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"applications/cvs/{instance.organization_id}/{uuid.uuid4()}.{ext}"


class Job(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"
        TEMPORARY = "temporary", "Temporary"

    class WorkMode(models.TextChoices):
        ONSITE = "onsite", "On-site"
        HYBRID = "hybrid", "Hybrid"
        REMOTE = "remote", "Remote"

    class ExperienceLevel(models.TextChoices):
        ENTRY = "entry", "Entry Level"
        JUNIOR = "junior", "Junior"
        MID = "mid", "Mid Level"
        SENIOR = "senior", "Senior"
        LEAD = "lead", "Lead"
        EXECUTIVE = "executive", "Executive"

    title = models.CharField(max_length=255)
    description = models.TextField()
    department = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=255, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WorkMode.choices,
        default=WorkMode.ONSITE,
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID,
    )
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default="USD")
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    vacancies = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["organization", "department"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_public(self):
        return self.status == self.Status.OPEN


class Application(BaseModel):
    class Stage(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.APPLIED,
    )
    is_shortlisted = models.BooleanField(default=False)
    cover_letter = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    years_of_experience = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(50)],
    )
    cv = models.FileField(
        upload_to=application_cv_upload_path,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"]),
        ],
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]
        unique_together = [("job", "candidate")]
        indexes = [
            models.Index(fields=["organization", "stage"]),
            models.Index(fields=["organization", "job"]),
            models.Index(fields=["organization", "is_shortlisted"]),
        ]

    def __str__(self):
        return f"{self.candidate.email} → {self.job.title}"

    def clean(self):
        super().clean()
        if self.job_id and self.organization_id and self.job.organization_id != self.organization_id:
            raise ValidationError({"job": "Job must belong to the same organization."})
        if self.candidate_id and self.candidate.account_type != "candidate":
            raise ValidationError({"candidate": "Only candidate accounts can apply to jobs."})
        if self.cv:
            max_size = 5 * 1024 * 1024
            if self.cv.size > max_size:
                raise ValidationError({"cv": "CV file must be 5MB or smaller."})
