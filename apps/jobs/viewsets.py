from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.accounts.permissions import HasPermission, IsCandidateUser, IsEmployerUser
from apps.common.permissions import IsOrganizationMember
from apps.common.responses import api_response
from apps.common.viewsets import BaseModelViewSet
from apps.jobs.filters import ApplicationFilter, JobFilter
from apps.jobs.models import Application, Job
from apps.jobs.selectors import get_application_neighbors
from apps.jobs.serializers import (
    ApplicationCreateSerializer,
    ApplicationDetailSerializer,
    ApplicationListSerializer,
    ApplicationUpdateSerializer,
    CandidateApplicationSerializer,
    JobCreateSerializer,
    JobDetailSerializer,
    JobListSerializer,
    JobUpdateSerializer,
    PublicJobDetailSerializer,
    PublicJobListSerializer,
)
from apps.jobs.services import ApplicationService, JobService


class JobViewSet(BaseModelViewSet):
    queryset = Job.objects.prefetch_related("applications")
    filterset_class = JobFilter
    search_fields = ["title", "location", "department"]
    ordering_fields = ["created_at", "title", "status", "application_deadline"]
    limit_resource = "jobs"
    serializer_class = JobDetailSerializer
    serializer_action_classes = {
        "list": JobListSerializer,
        "retrieve": JobDetailSerializer,
        "create": JobCreateSerializer,
        "update": JobDetailSerializer,
        "partial_update": JobDetailSerializer,
    }

    def get_permissions(self):
        permission_map = {
            "list": HasPermission("job.view"),
            "retrieve": HasPermission("job.view"),
            "create": HasPermission("job.add"),
            "update": HasPermission("job.change"),
            "partial_update": HasPermission("job.change"),
            "destroy": HasPermission("job.delete"),
        }
        permission_class = permission_map.get(self.action, HasPermission("job.view"))
        return [IsAuthenticated(), IsEmployerUser(), IsOrganizationMember(), permission_class()]

    def perform_create(self, serializer):
        organization = self.request.organization
        if self.limit_resource:
            from apps.subscriptions.services import SubscriptionService

            SubscriptionService.check_limit(organization, self.limit_resource)
        job = JobService.create_job(
            organization=organization,
            created_by=self.request.user,
            **serializer.validated_data,
        )
        serializer.instance = job

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = JobDetailSerializer(serializer.instance)
        return api_response(True, "Created successfully", data=detail.data, status=201)

    def perform_update(self, serializer):
        JobService.update_job(job=serializer.instance, **serializer.validated_data)
        serializer.instance.refresh_from_db()


class PublicJobViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PublicJobDetailSerializer
    pagination_class = None

    def get_queryset(self):
        organization = self.request.organization
        if organization is None:
            return Job.objects.none()
        return Job.objects.filter(
            organization=organization,
            status=Job.Status.OPEN,
        ).select_related("organization")

    def get_serializer_class(self):
        if self.action == "list":
            return PublicJobListSerializer
        return PublicJobDetailSerializer

    def list(self, request, *args, **kwargs):
        if request.organization is None:
            raise NotFound("Organization context is required.")
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return api_response(True, "Success", data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        if request.organization is None:
            raise NotFound("Organization context is required.")
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(True, "Success", data=serializer.data)


class ApplicationViewSet(BaseModelViewSet):
    queryset = Application.objects.select_related("job", "candidate", "candidate__candidate_profile")
    filterset_class = ApplicationFilter
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    search_fields = [
        "candidate__email",
        "candidate__username",
        "candidate__first_name",
        "candidate__last_name",
        "job__title",
        "phone",
    ]
    ordering_fields = ["applied_at", "stage", "created_at"]
    ordering = ["-applied_at"]
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = ApplicationDetailSerializer
    serializer_action_classes = {
        "list": ApplicationListSerializer,
        "retrieve": ApplicationDetailSerializer,
        "create": ApplicationCreateSerializer,
        "partial_update": ApplicationUpdateSerializer,
        "update": ApplicationUpdateSerializer,
    }

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsCandidateUser()]
        if self.action == "me":
            return [IsAuthenticated(), IsCandidateUser()]
        permission_map = {
            "list": HasPermission("candidate.view"),
            "retrieve": HasPermission("candidate.view"),
            "neighbors": HasPermission("candidate.view"),
            "partial_update": HasPermission("candidate.change"),
            "update": HasPermission("candidate.change"),
        }
        permission_class = permission_map.get(self.action, HasPermission("candidate.view"))
        return [IsAuthenticated(), IsEmployerUser(), IsOrganizationMember(), permission_class()]

    def get_queryset(self):
        organization = getattr(self.request, "organization", None)
        if organization is None:
            return Application.objects.none()
        return Application.objects.filter(organization=organization).select_related(
            "job", "candidate", "candidate__candidate_profile"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        organization = self.request.organization
        if organization is None:
            raise ValidationError({"detail": "Organization context is required."})
        application = ApplicationService.apply(
            organization=organization,
            job=serializer.validated_data["job"],
            candidate=self.request.user,
            **{k: v for k, v in serializer.validated_data.items() if k != "job"},
        )
        serializer.instance = application

    def create(self, request, *args, **kwargs):
        if request.organization is None:
            raise ValidationError({"detail": "Organization context is required."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = ApplicationDetailSerializer(serializer.instance, context={"request": request})
        return api_response(True, "Application submitted successfully", data=detail.data, status=201)

    def perform_update(self, serializer):
        ApplicationService.update_application(
            application=serializer.instance,
            **serializer.validated_data,
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()
        detail = ApplicationDetailSerializer(instance, context=self.get_serializer_context())
        return api_response(True, "Updated successfully", data=detail.data)

    @action(detail=True, methods=["get"])
    def neighbors(self, request, pk=None):
        instance = self.get_object()
        queryset = self.filter_queryset(self.get_queryset())
        data = get_application_neighbors(queryset=queryset, application_id=instance.pk)
        return api_response(True, "Success", data=data)

    def me(self, request):
        organization = request.organization
        if organization is None:
            raise ValidationError({"detail": "Organization context is required."})
        applications = Application.objects.filter(
            organization=organization,
            candidate=request.user,
        ).select_related("job", "organization")
        serializer = CandidateApplicationSerializer(
            applications, many=True, context={"request": request}
        )
        return api_response(True, "Success", data=serializer.data)
