from celery import shared_task
from config.utils import send_html_email


# email haruka iha kotuk (Celery); se falla, koko fali dala 3
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, template, context, to):
	ok = send_html_email(subject, template, context, to)
	if not ok:
		raise self.retry()
	return ok
