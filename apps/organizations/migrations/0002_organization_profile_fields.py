# Generated manually for organization profile fields

import apps.organizations.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="banner",
            field=models.ImageField(
                blank=True,
                upload_to=apps.organizations.models.org_banner_upload_path,
                validators=apps.organizations.models.IMAGE_VALIDATORS,
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="employee_size",
            field=models.CharField(
                blank=True,
                choices=[
                    ("1-10", "1–10"),
                    ("11-50", "11–50"),
                    ("51-200", "51–200"),
                    ("201-500", "201–500"),
                    ("500+", "500+"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="industry",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="organization",
            name="logo",
            field=models.ImageField(
                blank=True,
                upload_to=apps.organizations.models.org_logo_upload_path,
                validators=apps.organizations.models.IMAGE_VALIDATORS,
            ),
        ),
    ]
