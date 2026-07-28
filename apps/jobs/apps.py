from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.jobs"
    label = "jobs"

    def ready(self):
        from apps.common.bulk_actions.registry import register_bulk_handler
        from apps.jobs.bulk_handlers.change_stage import ApplicationsChangeStageHandler
        from apps.jobs.bulk_handlers.export import ApplicationsExportHandler

        register_bulk_handler("applications", "change_stage", ApplicationsChangeStageHandler)
        register_bulk_handler("applications", "export", ApplicationsExportHandler)
