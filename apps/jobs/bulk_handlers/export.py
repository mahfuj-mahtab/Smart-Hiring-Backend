import os
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.exceptions import ValidationError

from apps.common.bulk_actions.handlers.base import BaseBulkActionHandler
from apps.jobs.selectors import get_applications_bulk_queryset

EXPORT_COLUMNS = [
    ("Candidate Name", "candidate_name"),
    ("Email", "candidate_email"),
    ("Job Title", "job_title"),
    ("Phone", "phone"),
    ("Years of Experience", "years_of_experience"),
    ("Stage", "stage"),
    ("Shortlisted", "is_shortlisted"),
    ("Applied At", "applied_at"),
    ("LinkedIn", "linkedin_url"),
    ("Portfolio", "portfolio_url"),
    ("CV URL", "cv_url"),
]


class ApplicationsExportHandler(BaseBulkActionHandler):
    permission = "candidate.view"

    def validate_payload(self, payload):
        return payload or {}

    def resolve_queryset(self, *, organization, selection, user):
        return get_applications_bulk_queryset(organization=organization, selection=selection)

    def execute(self, *, job, queryset):
        batch_size = getattr(settings, "BULK_ACTION_BATCH_SIZE", 500)
        total = job.total_count

        export_dir = Path(settings.MEDIA_ROOT) / "exports" / str(job.organization_id)
        export_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{job.id}.xlsx"
        file_path = export_dir / filename

        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet("Applications")
        sheet.append([column[0] for column in EXPORT_COLUMNS])

        processed = 0
        batch = []
        for application in queryset.iterator(chunk_size=batch_size):
            batch.append(application)
            if len(batch) >= batch_size:
                self._append_rows(sheet, batch)
                processed += len(batch)
                self._update_progress(job, processed, total)
                batch = []

        if batch:
            self._append_rows(sheet, batch)
            processed += len(batch)
            self._update_progress(job, processed, total)

        workbook.save(file_path)

        relative_path = os.path.join("exports", str(job.organization_id), filename)
        return {
            "download_path": relative_path,
            "exported_count": processed,
            "filename": filename,
        }

    def _append_rows(self, sheet, applications):
        for application in applications:
            sheet.append(
                [
                    application.candidate.get_full_name() or application.candidate.username,
                    application.candidate.email,
                    application.job.title,
                    application.phone or "",
                    application.years_of_experience if application.years_of_experience is not None else "",
                    application.stage,
                    "Yes" if application.is_shortlisted else "No",
                    timezone.localtime(application.applied_at).strftime("%Y-%m-%d %H:%M"),
                    application.linkedin_url or "",
                    application.portfolio_url or "",
                    self._cv_url(application),
                ]
            )

    def _cv_url(self, application):
        if not application.cv:
            return ""
        return f"{settings.PUBLIC_API_URL}{application.cv.url}"

    def _update_progress(self, job, processed, total):
        progress = int((processed / total) * 100) if total else 100
        job.processed_count = processed
        job.progress = progress
        job.save(update_fields=["processed_count", "progress", "updated_at"])
