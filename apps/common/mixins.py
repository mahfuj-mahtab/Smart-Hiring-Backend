from rest_framework.exceptions import ValidationError

from apps.common.responses import api_response


class OrganizationScopedQuerysetMixin:
    organization_field = "organization"

    def get_queryset(self):
        queryset = super().get_queryset()
        organization = getattr(self.request, "organization", None)
        if organization is None:
            return queryset.none()
        return queryset.filter(**{self.organization_field: organization})


class ActionSerializerMixin:
    serializer_action_classes = {}

    def get_serializer_class(self):
        if self.action in self.serializer_action_classes:
            return self.serializer_action_classes[self.action]
        return super().get_serializer_class()


class ApiResponseMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Success", data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Success", data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return api_response(True, "Created successfully", data=serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_response(True, "Updated successfully", data=serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(True, "Deleted successfully", status=204)


class SubscriptionLimitMixin:
    limit_resource = None

    def perform_create(self, serializer):
        organization = getattr(self.request, "organization", None)
        if self.limit_resource and organization is not None:
            from apps.subscriptions.services import SubscriptionService

            SubscriptionService.check_limit(organization, self.limit_resource)
        super().perform_create(serializer)
