from rest_framework import serializers

from apps.common.models import BulkJob


class BulkActionSelectionSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=BulkJob.SelectionMode.choices)
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False,
    )
    filters = serializers.DictField(required=False, allow_empty=True)

    def validate(self, attrs):
        mode = attrs.get("mode")
        if mode == BulkJob.SelectionMode.IDS:
            if not attrs.get("ids"):
                raise serializers.ValidationError({"ids": "This field is required for ids mode."})
        elif mode == BulkJob.SelectionMode.FILTER:
            attrs.setdefault("filters", {})
        return attrs


class BulkActionCreateSerializer(serializers.Serializer):
    resource = serializers.CharField(max_length=64)
    action = serializers.CharField(max_length=64)
    selection = BulkActionSelectionSerializer()
    payload = serializers.DictField(required=False, allow_empty=True, default=dict)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class BulkJobSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = BulkJob
        fields = [
            "id",
            "resource",
            "action",
            "status",
            "progress",
            "total_count",
            "processed_count",
            "selection_mode",
            "result",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        if (
            obj.action == "export"
            and obj.status == BulkJob.Status.COMPLETED
            and obj.result.get("download_path")
        ):
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(f"/api/v1/bulk-actions/{obj.id}/download/")
        return None
