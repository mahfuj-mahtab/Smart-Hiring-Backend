from collections import defaultdict

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.models import Permission
from apps.accounts.permissions import HasPermission, IsCandidateUser, IsEmployerUser
from apps.accounts.selectors import get_active_member, get_user_permission_codenames
from apps.accounts.serializers import CandidateMeSerializer, MeSerializer, PermissionSerializer
from apps.common.permissions import IsOrganizationMember
from apps.common.responses import api_response


class PermissionListView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsEmployerUser,
        IsOrganizationMember,
        HasPermission("role.view"),
    ]

    def get(self, request):
        permissions = Permission.objects.all()
        grouped = defaultdict(list)
        for permission in permissions:
            grouped[permission.module].append(permission)

        data = [
            {"module": module, "permissions": PermissionSerializer(perms, many=True).data}
            for module, perms in sorted(grouped.items())
        ]
        return api_response(True, "Success", data=data)


class MeView(APIView):
    permission_classes = [IsAuthenticated, IsEmployerUser, IsOrganizationMember]

    def get(self, request):
        member = get_active_member(request.user, request.organization)
        organization = request.organization
        data = {
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.username,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "slug": organization.slug,
            },
            "role": {
                "id": member.role.id,
                "name": member.role.name,
            }
            if member
            else None,
            "permissions": get_user_permission_codenames(request.user, organization),
            "is_owner": member.is_owner if member else False,
        }
        serializer = MeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_response(True, "Success", data=serializer.data)


class CandidateMeView(APIView):
    permission_classes = [IsAuthenticated, IsCandidateUser]

    def get(self, request):
        profile = request.user.candidate_profile
        data = {
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.username,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "account_type": request.user.account_type,
            "phone": profile.phone,
        }
        serializer = CandidateMeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_response(True, "Success", data=serializer.data)
