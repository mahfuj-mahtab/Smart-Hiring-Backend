import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def org_logo_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"organizations/{instance.id}/logo/{uuid.uuid4()}.{ext}"


def org_banner_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"organizations/{instance.id}/banner/{uuid.uuid4()}.{ext}"


IMAGE_VALIDATORS = [
    FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
]


class Organization(models.Model):
    class EmployeeSize(models.TextChoices):
        SIZE_1_10 = "1-10", "1–10"
        SIZE_11_50 = "11-50", "11–50"
        SIZE_51_200 = "51-200", "51–200"
        SIZE_201_500 = "201-500", "201–500"
        SIZE_500_PLUS = "500+", "500+"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
    )
    logo = models.ImageField(
        upload_to=org_logo_upload_path,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )
    banner = models.ImageField(
        upload_to=org_banner_upload_path,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )
    industry = models.CharField(max_length=100, blank=True)
    employee_size = models.CharField(
        max_length=20,
        choices=EmployeeSize.choices,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        reserved = getattr(settings, "RESERVED_SUBDOMAINS", [])
        if self.slug in reserved:
            raise ValidationError({"slug": "This subdomain is reserved."})

    def save(self, *args, **kwargs):
        self.slug = self.slug.lower()
        self.full_clean()
        super().save(*args, **kwargs)
