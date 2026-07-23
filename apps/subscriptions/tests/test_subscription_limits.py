import pytest
from rest_framework.exceptions import ValidationError

from apps.accounts.models import OrganizationMember, Role
from apps.subscriptions.services import SubscriptionService


@pytest.mark.django_db
def test_member_under_limit_allowed(organization, member_user, owner_user):
    owner_role = Role.objects.get(organization=organization, name="Owner")
    OrganizationMember.objects.create(
        organization=organization,
        user=member_user,
        role=owner_role,
    )
    SubscriptionService.check_limit(organization, "members")


@pytest.mark.django_db
def test_member_at_limit_blocked(organization, owner_user):
    organization.subscription.plan.max_members = 1
    organization.subscription.plan.save()

    with pytest.raises(ValidationError) as exc_info:
        SubscriptionService.check_limit(organization, "members")
    assert "Plan limit reached" in str(exc_info.value)
