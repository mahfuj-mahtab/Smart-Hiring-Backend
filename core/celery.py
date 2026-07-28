import os

import django
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")

django.setup()

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)
