from django.conf import settings
from django.urls import reverse
from config.tasks import send_email_task


def kirim_email_konta_foun(user, pesoal):
	# Email ba utilizador foun: konta kria ona + password default
	send_email_task.delay(
		'SMKRE — Ita-nia konta kria ona',
		'auth/email/konta_foun.html',
		{'naran': pesoal.name, 'email': user.email, 'password': settings.DEFAULT_PASSWORD,
			'login_url': settings.SITE_URL + reverse('login')},
		[user.email])


def kirim_email_reset_admin(user, pesoal):
	# Email bainhira Admin reset password
	send_email_task.delay(
		'SMKRE — Password reset ona',
		'auth/email/reset_admin.html',
		{'naran': pesoal.name if pesoal else user.email, 'password': settings.DEFAULT_PASSWORD,
			'login_url': settings.SITE_URL + reverse('login')},
		[user.email])


def kirim_email_offline(user, pesoal, permission):
	send_email_task.delay(
		'SMKRE — Autorizasaun offline ativu',
		'auth/email/offline.html',
		{'naran': pesoal.name if pesoal else user.email, 'end_date': permission.end_date.strftime('%d/%m/%Y %H:%M')},
		[user.email])
