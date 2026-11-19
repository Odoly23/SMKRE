import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger('smkre')


# haruka email HTML (template iha templates/.../email/); uza iha Celery task
def send_html_email(subject, template, context, to):
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


# IP kliente loos (anti-spoof): iha kotuk Nginx, IP ikus iha X-Forwarded-For mak Nginx hatama
# (ida dahuluk bele falsu husi kliente); la iha proxy (dev) → REMOTE_ADDR
def get_client_ip(request):
	header = getattr(settings, 'CLIENT_IP_HEADER', '')
	if header and settings.BEHIND_PROXY and request.META.get(header):
		return request.META[header].split(',')[0].strip()
	xff = request.META.get('HTTP_X_FORWARDED_FOR')
	if xff and settings.BEHIND_PROXY:
		return xff.split(',')[-1].strip()
	return request.META.get('REMOTE_ADDR') or None
