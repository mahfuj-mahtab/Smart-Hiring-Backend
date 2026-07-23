import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
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
