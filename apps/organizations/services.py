from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import Role
from apps.accounts.services import MemberService, RoleService
from apps.organizations.models import Organization
from apps.subscriptions.services import SubscriptionService


class OrganizationService:
    @staticmethod
    @transaction.atomic
    def create_organization(*, name, slug, owner):
        if Organization.objects.filter(slug=slug).exists():
            raise ValidationError({"slug": "An organization with this subdomain already exists."})

        organization = Organization.objects.create(
            name=name,
            slug=slug.lower(),
            owner=owner,
        )

        owner_role = RoleService.create_role(
            organization=organization,
            name="Owner",
            is_system=True,
        )
        MemberService.create_member(
            organization=organization,
            user=owner,
            role=owner_role,
            is_owner=True,
            created_by=owner,
        )
        SubscriptionService.create_default_subscription(organization)
        return organization
