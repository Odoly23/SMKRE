from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from config.rbac import INVESTIGADOR, ADMIN, SUPERADMIN
from custom.models import Munisipiu, Suku
from users.models import Pesoal, PesoalUser

PASSWORD = 'Teste#Online-2026'
KONTA = [  # (email, papél, naran)
	('teste.investigador@redebarai.org', INVESTIGADOR, 'Investigadór Teste'),
	('teste.admin@redebarai.org', ADMIN, 'Admin Teste'),
	('teste.superadmin@redebarai.org', SUPERADMIN, 'Superadmin Teste'),
]


class Command(BaseCommand):
	help = ("Prepara teste fluxu ONLINE iha laptop: konta teste Investigadór, Admin no Superadmin. "
		"La'o iha DEBUG deit (labele uza iha production).")

	def add_arguments(self, parser):
		parser.add_argument('--munisipiu', default='LIQ', help='Munisípiu knaar Investigadór (ex. LIQ, DIL)')

	@transaction.atomic
	def handle(self, *args, **opt):
		if not settings.DEBUG:
			raise CommandError('Komandu teste ne\'e permite deit iha DEBUG=True.')
		mun = Munisipiu.objects.filter(code=opt['munisipiu'].upper()).first()
		if not mun:
			raise CommandError(f'Munisípiu {opt["munisipiu"]} la iha. Halo uluk: python manage.py setup_smkre')
		# Formuláriu presiza suku atu haruka: se munisípiu seidauk iha suku, kria suku teste ida
		if not Suku.objects.filter(postu__munisipiu=mun).exists():
			postu = mun.postuadministrativu_set.first()
			Suku.objects.create(code=f'{mun.code}-TESTE', name='[TESTE] Suku', postu=postu)
			self.stdout.write(self.style.WARNING(f'Suku teste kria iha {postu} (seidauk iha lista suku ofisiál).'))

		for email, papel, naran in KONTA:
			user, _c = User.objects.get_or_create(username=email, defaults={'email': email})
			user.set_password(PASSWORD)
			user.is_active = True
			user.save()
			user.groups.set([Group.objects.get_or_create(name=papel)[0]])
			pesoal = Pesoal.objects.filter(email=email).first() or Pesoal.objects.create(name=naran, email=email, sexo='Feto')
			pesoal.munisipiu = mun if papel == INVESTIGADOR else pesoal.munisipiu
			pesoal.save()
			PesoalUser.objects.update_or_create(user=user, defaults={'pesoal': pesoal, 'must_change_password': False})

		self.stdout.write(self.style.SUCCESS('Prontu ba teste fluxu online (password hotu: %s):' % PASSWORD))
		self.stdout.write('  Investigadór : teste.investigador@redebarai.org  (munisípiu %s)' % mun.name)
		self.stdout.write('  Admin        : teste.admin@redebarai.org')
		self.stdout.write('  Superadmin   : teste.superadmin@redebarai.org')
		self.stdout.write('  1. Investigadór → Kazu Foun → prenxe → "Rai no Haruka ba Verifikasaun"')
		self.stdout.write('  2. Admin → 🔔 → loke kazu → Verifika')
		self.stdout.write('  3. Superadmin → 🔔 → loke kazu → Aprova  → mosu iha Dashboard + Portal')
		self.stdout.write('  Verifika: python manage.py cek_kazu')
