from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import Permission
from apps.accounts.services import MemberService, RoleService
from apps.organizations.models import Organization
from apps.subscriptions.services import SubscriptionService


class OrganizationService:
    @staticmethod
    def _delete_file(file_field):
        if file_field:
            file_field.delete(save=False)

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

        org_permission_ids = list(
            Permission.objects.filter(module="organization").values_list("id", flat=True)
        )
        owner_role = RoleService.create_role(
            organization=organization,
            name="Owner",
            permission_ids=org_permission_ids,
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

    @staticmethod
    @transaction.atomic
    def update_organization(*, organization, data):
        file_fields = ("logo", "banner")
        for field in file_fields:
            if field in data:
                new_file = data[field]
                old_file = getattr(organization, field)
                if new_file is not None and old_file:
                    OrganizationService._delete_file(old_file)

        for field, value in data.items():
            setattr(organization, field, value)

        organization.save()
        return organization
