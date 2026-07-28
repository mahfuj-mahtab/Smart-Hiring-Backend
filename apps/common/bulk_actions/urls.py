from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.common.bulk_actions.viewsets import BulkActionViewSet

router = DefaultRouter()
router.register("bulk-actions", BulkActionViewSet, basename="bulk-action")

urlpatterns = [
    path("", include(router.urls)),
]
