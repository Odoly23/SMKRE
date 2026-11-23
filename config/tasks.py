import logging
from celery import shared_task
from config.utils import send_html_email

logger = logging.getLogger('smkre')


# email haruka iha kotuk (Celery); se falla, koko fali dala 3.
# Modu eager (la iha worker Celery, ex. cPanel / PythonAnywhere): la koko fali — rejista erru de'it,
# atu email falla la halo pájina (ex. kria utilizador) sai erru 500. Dadus rai ona iha database.
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, template, context, to):
	ok = send_html_email(subject, template, context, to)
	if not ok:
		if self.request.is_eager:
			logger.warning('Email la bele haruka (%s → %s). Verifika EMAIL_* iha .env: python manage.py cek_email', subject, to)
			return False
		raise self.retry()
	return ok
