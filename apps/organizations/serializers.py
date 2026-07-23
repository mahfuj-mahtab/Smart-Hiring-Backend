from rest_framework import serializers

from apps.organizations.models import Organization

MAX_LOGO_SIZE = 2 * 1024 * 1024
MAX_BANNER_SIZE = 5 * 1024 * 1024


class OrganizationSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    employee_size_display = serializers.CharField(
        source="get_employee_size_display",
        read_only=True,
    )

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "banner",
            "industry",
            "employee_size",
            "employee_size_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_logo(self, obj):
        if not obj.logo:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return obj.logo.url

    def get_banner(self, obj):
        if not obj.banner:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.banner.url)
        return obj.banner.url


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name", "industry", "employee_size", "logo", "banner"]

    def validate_logo(self, value):
        if value and value.size > MAX_LOGO_SIZE:
            raise serializers.ValidationError("Logo must be 2 MB or smaller.")
        return value

    def validate_banner(self, value):
        if value and value.size > MAX_BANNER_SIZE:
            raise serializers.ValidationError("Banner must be 5 MB or smaller.")
        return value


class PublicOrganizationSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    employee_size_display = serializers.CharField(
        source="get_employee_size_display",
        read_only=True,
    )

    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "logo",
            "banner",
            "industry",
            "employee_size",
            "employee_size_display",
        ]

    def get_logo(self, obj):
        if not obj.logo:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.logo.url)
        return obj.logo.url

    def get_banner(self, obj):
        if not obj.banner:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.banner.url)
        return obj.banner.url
