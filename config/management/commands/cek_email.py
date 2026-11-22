"""Diagnóstiku email: haree pasu ida-idak (konfigurasaun → DNS → koneksaun → SSL/TLS → login → haruka).
Uza:  python manage.py cek_email naran@exemplu.tl
Password la hatudu (hatudu de'it "iha" ka "mamuk")."""
import smtplib
import socket
import ssl
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	help = "Verifika konfigurasaun email pasu-ba-pasu no haruka email teste."

	# parámetru: email simu-na'in ba teste
	def add_arguments(self, parser):
		parser.add_argument('ba', help="Email ne'ebé sei simu email teste")

	# hatudu rezultadu pasu ida (OK / SALA + dalan hadia)
	def pasu(self, n, testu, ok, detalla=''):
		marka = self.style.SUCCESS('OK  ') if ok else self.style.ERROR('SALA')
		self.stdout.write(f'[{n}] {marka} {testu}' + (f'\n      → {detalla}' if detalla else ''))

	# hala'o diagnóstiku tomak
	def handle(self, *args, **opt):
		s = settings
		host, port = s.EMAIL_HOST, s.EMAIL_PORT
		ssl_ = getattr(s, 'EMAIL_USE_SSL', False)
		self.stdout.write(f'Backend: {s.EMAIL_BACKEND}\nHost: {host}  Port: {port}  SSL: {ssl_}  TLS: {s.EMAIL_USE_TLS}\n'
			f'User: {s.EMAIL_HOST_USER or "(mamuk)"}  Password: {"iha" if s.EMAIL_HOST_PASSWORD else "(MAMUK)"}\n'
			f'Husi: {s.DEFAULT_FROM_EMAIL}\n')

		# 1. konfigurasaun
		if 'smtp' not in s.EMAIL_BACKEND:
			return self.pasu(1, "EMAIL_BACKEND la'ós SMTP", False,
				'Email la haruka, hatudu de\'it iha log. Iha .env: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend, depois Reload.')
		if port == 465 and not ssl_:
			return self.pasu(1, 'Port 465 maibé EMAIL_USE_SSL=False', False,
				'Port 465 presiza SSL. Iha .env: EMAIL_USE_SSL=True no EMAIL_USE_TLS=False (no git pull kódigu foun).')
		if not s.EMAIL_HOST_USER or not s.EMAIL_HOST_PASSWORD:
			return self.pasu(1, 'User ka password email mamuk', False, 'Hatama EMAIL_HOST_USER no EMAIL_HOST_PASSWORD iha .env.')
		from email.utils import parseaddr
		husi = parseaddr(s.DEFAULT_FROM_EMAIL)[1]
		if husi.lower() != s.EMAIL_HOST_USER.lower():
			self.stdout.write(self.style.WARNING(f'[1] AVIZU DEFAULT_FROM_EMAIL ({husi}) la hanesan EMAIL_HOST_USER ({s.EMAIL_HOST_USER})')
				+ f'\n      → Server cPanel bele rejeita. Iha .env: DEFAULT_FROM_EMAIL=SIBAR - RbR <{s.EMAIL_HOST_USER}>')
		self.pasu(1, 'Konfigurasaun', True)

		# 2. DNS
		try:
			ip = socket.gethostbyname(host)
		except OSError as e:
			return self.pasu(2, f'DNS: la hetan {host}', False, f'{e}. Verifika naran server (cPanel → Connect Devices).')
		self.pasu(2, f'DNS: {host} = {ip}', True)

		# 3. koneksaun TCP
		try:
			sock = socket.create_connection((host, port), timeout=15)
			sock.close()
		except OSError as e:
			return self.pasu(3, f'Koneksaun ba {host}:{port}', False,
				f'{e}. Server hosting blokeia koneksaun SMTP ba li\'ur (ex. PythonAnywhere konta gratis: SMTP '
				f'permite de\'it ba server balu, ex. Gmail). Solusaun: konta selu ka uza Gmail App Password.')
		self.pasu(3, f'Koneksaun ba {host}:{port}', True)

		# 4. SSL/TLS + 5. login
		try:
			if ssl_:
				srv = smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context())
			else:
				srv = smtplib.SMTP(host, port, timeout=20)
				if s.EMAIL_USE_TLS:
					srv.starttls(context=ssl.create_default_context())
		except (ssl.SSLError, smtplib.SMTPException, OSError) as e:
			return self.pasu(4, 'SSL/TLS', False, f'{e}. Port 465 → SSL=True/TLS=False; port 587 → SSL=False/TLS=True.')
		self.pasu(4, 'SSL/TLS', True)
		try:
			srv.login(s.EMAIL_HOST_USER, s.EMAIL_HOST_PASSWORD)
		except smtplib.SMTPAuthenticationError as e:
			srv.close()
			return self.pasu(5, 'Login', False, f'{e.smtp_code} {e.smtp_error!r}. Password sala: koko login iha webmail ho password hanesan.')
		except smtplib.SMTPException as e:
			srv.close()
			return self.pasu(5, 'Login', False, str(e))
		srv.quit()
		self.pasu(5, f'Login {s.EMAIL_HOST_USER}', True)

		# 6. haruka email teste
		try:
			send_mail('SIBAR-RbR: teste email', 'Email teste husi SIBAR-RbR. Se simu ida ne\'e, konfigurasaun email di\'ak.',
				s.DEFAULT_FROM_EMAIL, [opt['ba']], fail_silently=False)
		except Exception as e:
			return self.pasu(6, 'Haruka', False, f'{type(e).__name__}: {e}. DEFAULT_FROM_EMAIL tenke hanesan EMAIL_HOST_USER ({s.EMAIL_HOST_USER}).')
		self.pasu(6, f'Haruka ba {opt["ba"]}', True, 'Haree inbox (no folder Spam).')
