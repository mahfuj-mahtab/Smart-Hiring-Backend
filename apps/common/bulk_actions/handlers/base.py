class BaseBulkActionHandler:
    permission: str = ""

    def validate_payload(self, payload):
        return payload or {}

    def resolve_queryset(self, *, organization, selection, user):
        raise NotImplementedError

    def execute(self, *, job, queryset):
        raise NotImplementedError
