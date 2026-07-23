from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        read_only_fields = ("id", "organization", "created_at", "updated_at", "created_by")
