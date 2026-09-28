import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger('smkre')


def send_html_email(subject, template, context, to):
	# Haruka email HTML (template iha templates/.../email/). Uza iha Celery task.
	ctx = {'site_url': settings.SITE_URL, **context}
	html = render_to_string(template, ctx)
	msg = EmailMultiAlternatives(subject, strip_tags(html), settings.DEFAULT_FROM_EMAIL, to)
	msg.attach_alternative(html, 'text/html')
	try:
		msg.send()
		return True
	except Exception as e:
		logger.error(f'Email la haruka ba {to}: {e}')
		return False


def get_client_ip(request):
	# Iha kotuk Nginx: IP ikus iha X-Forwarded-For mak Nginx rasik hatama (ida dahuluk bele falsu husi kliente).
	# La iha proxy (dev): REMOTE_ADDR.
	xff = request.META.get('HTTP_X_FORWARDED_FOR')
	if xff and settings.BEHIND_PROXY:
		return xff.split(',')[-1].strip()
	return request.META.get('REMOTE_ADDR') or None
