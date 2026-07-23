from rest_framework import serializers

from apps.accounts.models import OrganizationMember, Permission, Role, User
from apps.common.serializers import BaseModelSerializer


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "module", "action", "label"]


class PermissionMatrixSerializer(serializers.Serializer):
    module = serializers.CharField()
    permissions = PermissionSerializer(many=True)


class RoleListSerializer(serializers.ModelSerializer):
    permission_count = serializers.IntegerField(source="permissions.count", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "is_system", "permission_count", "created_at", "updated_at"]


class RoleDetailSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "is_system",
            "permissions",
            "permission_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]


class RoleCreateSerializer(serializers.ModelSerializer):
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )

    class Meta:
        model = Role
        fields = ["name", "permission_ids"]


class OrganizationMemberListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = OrganizationMember
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "role",
            "role_name",
            "is_owner",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class OrganizationMemberDetailSerializer(OrganizationMemberListSerializer):
    class Meta(OrganizationMemberListSerializer.Meta):
        fields = OrganizationMemberListSerializer.Meta.fields


class OrganizationMemberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMember
        fields = ["user", "role", "is_active"]

    def validate_user(self, value):
        organization = self.context["request"].organization
        if OrganizationMember.objects.filter(organization=organization, user=value).exists():
            raise serializers.ValidationError("User is already a member of this organization.")
        if value.account_type != User.AccountType.EMPLOYER:
            raise serializers.ValidationError("Only employer accounts can be organization members.")
        return value


class OrganizationMemberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMember
        fields = ["role", "is_active"]


class MeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    organization = serializers.DictField()
    role = serializers.DictField(allow_null=True)
    permissions = serializers.ListField(child=serializers.CharField())
    is_owner = serializers.BooleanField()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")
    organization_name = serializers.CharField(max_length=255)
    organization_slug = serializers.SlugField(max_length=100)

    def validate_organization_slug(self, value):
        from django.conf import settings

        slug = value.lower()
        reserved = getattr(settings, "RESERVED_SUBDOMAINS", [])
        if slug in reserved:
            raise serializers.ValidationError("This subdomain is reserved.")
        return slug

    def validate_email(self, value):
        existing = User.objects.filter(email__iexact=value).first()
        if existing:
            if existing.account_type == User.AccountType.CANDIDATE:
                raise serializers.ValidationError(
                    "This email is registered as a candidate account."
                )
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        existing = User.objects.filter(username__iexact=value).first()
        if existing:
            if existing.account_type == User.AccountType.CANDIDATE:
                raise serializers.ValidationError(
                    "This username is registered as a candidate account."
                )
            raise serializers.ValidationError("A user with this username already exists.")
        return value


class CandidateRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")
    phone = serializers.CharField(max_length=30, required=False, default="")

    def validate_email(self, value):
        existing = User.objects.filter(email__iexact=value).first()
        if existing:
            if existing.account_type == User.AccountType.EMPLOYER:
                raise serializers.ValidationError(
                    "This email is registered as an employer account."
                )
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        existing = User.objects.filter(username__iexact=value).first()
        if existing:
            if existing.account_type == User.AccountType.EMPLOYER:
                raise serializers.ValidationError(
                    "This username is registered as an employer account."
                )
            raise serializers.ValidationError("A user with this username already exists.")
        return value


class CandidateMeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    username = serializers.CharField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    account_type = serializers.CharField()
    phone = serializers.CharField(allow_blank=True)
