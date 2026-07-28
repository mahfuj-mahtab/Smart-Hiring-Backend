from celery import shared_task

from apps.common.bulk_actions.services import BulkActionService


@shared_task(bind=True, max_retries=0)
def run_bulk_job_task(self, job_id):
    BulkActionService.run_job(job_id)
