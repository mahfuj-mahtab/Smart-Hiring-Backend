from rest_framework.permissions import BasePermission


class IsOrganizationMember(BasePermission):
    message = "You are not a member of this organization."

    def has_permission(self, request, view):
        organization = getattr(request, "organization", None)
        if organization is None:
          return False
        if not request.user or not request.user.is_authenticated:
          return False

        from apps.accounts.selectors import get_active_member

        return get_active_member(request.user, organization) is not None


class IsOrganizationOwner(BasePermission):
    message = "Only the organization owner can perform this action."

    def has_permission(self, request, view):
        organization = getattr(request, "organization", None)
        if organization is None:
          return False
        if not request.user or not request.user.is_authenticated:
          return False

        from apps.accounts.selectors import get_active_member

        member = get_active_member(request.user, organization)
        return member is not None and member.is_owner
