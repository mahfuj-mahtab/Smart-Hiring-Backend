from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import CandidateProfile, OrganizationMember, Permission, Role, User


class RoleService:
    @staticmethod
    @transaction.atomic
    def create_role(*, organization, name, permission_ids=None, is_system=False, created_by=None):
        if Role.objects.filter(organization=organization, name=name).exists():
            raise ValidationError({"name": "A role with this name already exists."})

        role = Role.objects.create(
            organization=organization,
            name=name,
            is_system=is_system,
        )
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        return role

    @staticmethod
    @transaction.atomic
    def update_role(*, role, name=None, permission_ids=None):
        if name is not None:
            if (
                Role.objects.filter(organization=role.organization, name=name)
                .exclude(pk=role.pk)
                .exists()
            ):
                raise ValidationError({"name": "A role with this name already exists."})
            role.name = name

        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)

        role.save()
        return role


class MemberService:
    @staticmethod
    @transaction.atomic
    def create_member(*, organization, user, role, is_owner=False, created_by=None):
        if OrganizationMember.objects.filter(organization=organization, user=user).exists():
            raise ValidationError({"user": "User is already a member of this organization."})

        if user.account_type != User.AccountType.EMPLOYER:
            raise ValidationError({"user": "Only employer accounts can be organization members."})

        return OrganizationMember.objects.create(
            organization=organization,
            user=user,
            role=role,
            is_owner=is_owner,
            created_by=created_by,
        )

    @staticmethod
    @transaction.atomic
    def update_member(*, member, role=None, is_active=None):
        if role is not None:
            member.role = role
        if is_active is not None:
            member.is_active = is_active
        member.save()
        return member


class CandidateService:
    @staticmethod
    @transaction.atomic
    def register_candidate(*, email, username, password, first_name="", last_name="", phone=""):
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError({"email": "A user with this email already exists."})
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError({"username": "A user with this username already exists."})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            account_type=User.AccountType.CANDIDATE,
        )
        profile = CandidateProfile.objects.create(user=user, phone=phone)
        return user, profile
