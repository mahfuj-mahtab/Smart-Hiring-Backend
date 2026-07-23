from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import User
from apps.accounts.serializers import CandidateRegisterSerializer, RegisterSerializer
from apps.accounts.services import CandidateService
from apps.common.responses import api_response
from apps.organizations.services import OrganizationService

UserModel = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = UserModel.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            account_type=User.AccountType.EMPLOYER,
        )

        organization = OrganizationService.create_organization(
            name=data["organization_name"],
            slug=data["organization_slug"],
            owner=user,
        )

        token_serializer = TokenObtainPairSerializer(
            data={"username": data["username"], "password": data["password"]}
        )
        token_serializer.is_valid(raise_exception=True)

        return api_response(
            success=True,
            message="Registration successful",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "account_type": user.account_type,
                },
                "organization": {
                    "id": organization.id,
                    "name": organization.name,
                    "slug": organization.slug,
                },
                "tokens": token_serializer.validated_data,
            },
            status=status.HTTP_201_CREATED,
        )


class CandidateRegisterView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = CandidateRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, profile = CandidateService.register_candidate(
            email=data["email"],
            username=data["username"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            phone=data.get("phone", ""),
        )

        token_serializer = TokenObtainPairSerializer(
            data={"username": data["username"], "password": data["password"]}
        )
        token_serializer.is_valid(raise_exception=True)

        return api_response(
            success=True,
            message="Candidate registration successful",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "account_type": user.account_type,
                },
                "profile": {
                    "id": profile.id,
                    "phone": profile.phone,
                },
                "tokens": token_serializer.validated_data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                success=True,
                message="Login successful",
                data={"tokens": response.data},
            )
        return response


class RefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                success=True,
                message="Token refreshed",
                data={"tokens": response.data},
            )
        return response
