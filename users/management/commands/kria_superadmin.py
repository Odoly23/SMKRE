import getpass
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from config.rbac import SUPERADMIN
from users.models import Pesoal, PesoalUser


class Command(BaseCommand):
	help = "Kria Superadmin dahuluk (User + Pesoal + role superadmin)."

	def add_arguments(self, parser):
		parser.add_argument('--email', required=True)
		parser.add_argument('--naran', required=True)
		parser.add_argument('--password', help="Se la fó, sistema sei husu (la hatudu iha ekran).")

	@transaction.atomic
	def handle(self, *args, **options):
		email = options['email'].strip().lower()
		if User.objects.filter(username=email).exists():
			raise CommandError(f'Utilizador {email} iha ona.')
		password = options.get('password') or getpass.getpass('Password: ')
		if password == settings.DEFAULT_PASSWORD:
			raise CommandError('Superadmin labele uza password default.')
		try:
			validate_password(password)
		except ValidationError as e:
			raise CommandError(' '.join(e.messages))
		user = User.objects.create_user(username=email, email=email, password=password,
			first_name=options['naran'][:150], is_staff=True, is_superuser=True)
		user.groups.add(Group.objects.get_or_create(name=SUPERADMIN)[0])
		pesoal = Pesoal.objects.create(name=options['naran'], email=email)
		PesoalUser.objects.create(pesoal=pesoal, user=user, must_change_password=False)
		self.stdout.write(self.style.SUCCESS(f'Superadmin kria ona: {email}'))
