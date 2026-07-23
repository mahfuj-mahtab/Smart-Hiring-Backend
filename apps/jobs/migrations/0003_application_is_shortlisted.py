# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_application_cv_application_linkedin_url_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="is_shortlisted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name="application",
            index=models.Index(
                fields=["organization", "is_shortlisted"],
                name="jobs_applic_organiz_short_idx",
            ),
        ),
    ]
