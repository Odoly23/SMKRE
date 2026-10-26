from django.conf import settings
from django.urls import reverse
from config.tasks import send_email_task


def kirim_email_konta_foun(user, pesoal):
	# Email ba utilizador foun: konta kria ona + password default
	send_email_task.delay(
		'SIBAR-RbR — Ita-nia konta kria ona',
		'auth/email/konta_foun.html',
		{'naran': pesoal.name, 'email': user.email, 'password': settings.DEFAULT_PASSWORD,
			'login_url': settings.SITE_URL + reverse('login')},
		[user.email])


def kirim_email_reset_admin(user, pesoal):
	# Email bainhira Admin reset password
	send_email_task.delay(
		'SIBAR-RbR — Password reset ona',
		'auth/email/reset_admin.html',
		{'naran': pesoal.name if pesoal else user.email, 'password': settings.DEFAULT_PASSWORD,
			'login_url': settings.SITE_URL + reverse('login')},
		[user.email])


def kirim_email_offline(user, pesoal, permission, pin=None):
	"""Email autorizasaun offline: username, password default (se seidauk troka) no PIN app.
	pin=None (renova) → PIN la muda: email la hatudu PIN. Email falla la blokeia autorizasaun (log de'it)."""
	pu = getattr(user, 'pesoaluser', None)
	try:
		send_email_task.delay(
			'SIBAR-RbR — Autorizasaun input ativu',
			'auth/email/offline.html',
			{'naran': pesoal.name if pesoal else user.email, 'end_date': permission.end_date.strftime('%d/%m/%Y %H:%M'),
				'username': user.username, 'pin': pin,
				'password': settings.DEFAULT_PASSWORD if (pu and pu.must_change_password) else None,
				'app_url': settings.SITE_URL + reverse('sinkron')},
			[user.email])
	except Exception:
		import logging
		logging.getLogger('smkre').exception(f'Email autorizasaun la haruka: {user.email}')
