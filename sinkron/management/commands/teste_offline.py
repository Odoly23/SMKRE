from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from config.rbac import INVESTIGADOR, ADMIN, SUPERADMIN
from custom.models import Munisipiu
from users.models import Pesoal, PesoalUser
from users.services import give_offline


class Command(BaseCommand):
	help = ("Prepara teste app offline iha laptop: Investigadór teste + autorizasaun offline loron 7. "
		"La'o iha DEBUG deit (labele uza iha production).")

	def add_arguments(self, parser):
		parser.add_argument('--email', default='teste.offline@redebarai.org')
		parser.add_argument('--password', default='Teste#Offline-2026')
		parser.add_argument('--munisipiu', default='LIQ', help='Kódigu munisípiu knaar (ex. LIQ, DIL)')

	@transaction.atomic
	def handle(self, *args, **opt):
		if not settings.DEBUG:
			raise CommandError('Komandu teste ne\'e permite deit iha DEBUG=True.')
		mun = Munisipiu.objects.filter(code=opt['munisipiu'].upper()).first()
		if not mun:
			raise CommandError(f'Munisípiu {opt["munisipiu"]} la iha. Halo uluk: python manage.py setup_smkre')
		email = opt['email'].strip().lower()
		user, foun = User.objects.get_or_create(username=email, defaults={'email': email})
		user.set_password(opt['password'])
		user.is_active = True
		user.save()
		user.groups.set([Group.objects.get_or_create(name=INVESTIGADOR)[0]])
		pesoal = Pesoal.objects.filter(email=email).first() or Pesoal.objects.create(name='Investigadór Teste Offline', email=email, sexo='Feto', munisipiu=mun)
		pesoal.munisipiu = mun
		pesoal.save()
		PesoalUser.objects.update_or_create(user=user, defaults={'pesoal': pesoal, 'must_change_password': False})
		admin = User.objects.filter(groups__name__in=[ADMIN, SUPERADMIN], is_active=True).first()
		perm = give_offline(user, by=admin, note='Teste offline (laptop)')

		self.stdout.write(self.style.SUCCESS('Prontu ba teste app offline:'))
		self.stdout.write(f'  1. Loke      : http://127.0.0.1:8000/sinkron/  (Chrome, iha laptop)')
		self.stdout.write(f'  2. Login     : {email}  /  {opt["password"]}')
		self.stdout.write(f'  3. Munisípiu : {mun.name}  ·  autorizasaun to\'o {timezone.localtime(perm.end_date):%d/%m/%Y %H:%M}')
		self.stdout.write( '  4. DevTools (F12) → Network → Offline → rejista kazu → Prontu')
		self.stdout.write( '  5. Network → No throttling (online) → sinkron automátiku')
		self.stdout.write( '  6. Verifika : python manage.py cek_sinkron')
