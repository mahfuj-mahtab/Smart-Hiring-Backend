from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.jobs.viewsets import ApplicationViewSet, JobViewSet, PublicJobViewSet

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="job")
router.register("public/jobs", PublicJobViewSet, basename="public-job")
router.register("applications", ApplicationViewSet, basename="application")

urlpatterns = [
    path(
        "applications/me/",
        ApplicationViewSet.as_view({"get": "me"}),
        name="application-me",
    ),
    path("", include(router.urls)),
]
