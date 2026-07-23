from rest_framework.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import OrganizationMember
from apps.jobs.models import Job
from apps.subscriptions.models import Plan, Subscription


class SubscriptionService:
    RESOURCE_COUNTERS = {
        "members": lambda organization: OrganizationMember.objects.filter(
            organization=organization,
            is_active=True,
        ).count(),
        "jobs": lambda organization: Job.objects.filter(organization=organization).count(),
    }

    @staticmethod
    def create_default_subscription(organization):
        plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "max_members": 5,
                "max_jobs": 10,
                "is_active": True,
            },
        )
        return Subscription.objects.create(
            organization=organization,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            starts_at=timezone.now(),
        )

    @staticmethod
    def check_limit(organization, resource):
        if resource not in SubscriptionService.RESOURCE_COUNTERS:
            raise ValidationError({"detail": f"Unknown subscription resource: {resource}"})

        try:
            subscription = organization.subscription
        except Subscription.DoesNotExist:
            raise ValidationError({"detail": "No active subscription found for this organization."})

        if subscription.status != Subscription.Status.ACTIVE:
            raise ValidationError({"detail": "Subscription is not active."})

        plan = subscription.plan
        limit_field = f"max_{resource}"
        max_allowed = getattr(plan, limit_field, None)
        if max_allowed is None:
            return

        current_count = SubscriptionService.RESOURCE_COUNTERS[resource](organization)
        if current_count >= max_allowed:
            raise ValidationError(
                {
                    "detail": f"Plan limit reached for {resource}. Maximum allowed: {max_allowed}."
                }
            )
