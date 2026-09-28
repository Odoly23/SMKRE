from django.contrib.auth.models import User
from django.utils import translation
from config.tasks import send_email_task
from notification.models import Notification


def _lian(user):
	pu = getattr(user, 'pesoaluser', None)
	return getattr(getattr(pu, 'pesoal', None), 'lian', None) or 'tet'


def kirim_notif(user, tipu, message, url='', actor=None, urgent=False, email=False):
	# Kria notifikasaun ba utilizador ida (🔔) no, se presiza, haruka email.
	# message bele funsaun (lambda) → hakerek iha lian simu-na'in nian
	if callable(message):
		with translation.override(_lian(user)):
			message = str(message())
	obj = Notification.objects.create(recipient=user, actor=actor, tipu=tipu, message=message[:255], url=url, is_urgent=urgent)
	if email and user.email:
		subject = ('[URJENTE] ' if urgent else '') + 'SMKRE — ' + message[:80]
		send_email_task.delay(subject, 'notification/email/notif.html',
			{'message': message, 'url': url, 'urgent': urgent}, [user.email])
	return obj


def kirim_notif_role(roles, tipu, message, url='', actor=None, urgent=False, email=True, exclude=None):
	# Notifikasaun ba utilizador ativu hotu iha role sira (ezemplu: Admin + Superadmin)
	users = User.objects.filter(groups__name__in=roles, is_active=True).distinct()
	if exclude:
		users = users.exclude(pk=exclude.pk)
	return [kirim_notif(u, tipu, message, url, actor, urgent, email) for u in users]
