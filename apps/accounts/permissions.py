from rest_framework.permissions import BasePermission

from apps.accounts.models import User
from apps.accounts.selectors import get_active_member, user_has_permission


class IsEmployerUser(BasePermission):
    message = "This endpoint is only available to employer accounts."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.account_type == User.AccountType.EMPLOYER
        )


class IsCandidateUser(BasePermission):
    message = "This endpoint is only available to candidate accounts."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.account_type == User.AccountType.CANDIDATE
        )


def HasPermission(codename):
    class _HasPermission(BasePermission):
        message = f"Permission required: {codename}"

        def has_permission(self, request, view):
            organization = getattr(request, "organization", None)
            if organization is None:
                return False
            if not request.user or not request.user.is_authenticated:
                return False
            return user_has_permission(request.user, organization, codename)

    return _HasPermission
