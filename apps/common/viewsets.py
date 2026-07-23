from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from apps.common.mixins import (
    ActionSerializerMixin,
    ApiResponseMixin,
    OrganizationScopedQuerysetMixin,
    SubscriptionLimitMixin,
)
from apps.common.pagination import StandardPagination
from apps.common.permissions import IsOrganizationMember


class BaseModelViewSet(
    OrganizationScopedQuerysetMixin,
    ActionSerializerMixin,
    ApiResponseMixin,
    SubscriptionLimitMixin,
    viewsets.ModelViewSet,
):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        organization = self.request.organization
        if self.limit_resource and organization is not None:
            from apps.subscriptions.services import SubscriptionService

            SubscriptionService.check_limit(organization, self.limit_resource)
        serializer.save(
            organization=organization,
            created_by=self.request.user,
        )
