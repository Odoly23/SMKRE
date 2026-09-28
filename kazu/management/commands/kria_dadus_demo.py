import random
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from config.rbac import INVESTIGADOR
from custom.models import Munisipiu, TipuKonflitu, TipuRai, TipuEviksaun, TipuAtor, NesesidadeUrjente, EstraguPatrimoniu
from kazu.models import Kazu, UmaKainAfetada, InsidenteEviksaun, AtorEnvolvidu, KazuHistoria
from kazu.services import generate_kode
from users.models import Pesoal, PesoalUser

STATUS_PESU = [('SYNCED', 25), ('VERIFIED', 20), ('APPROVED', 25), ('COMPLETED', 15), ('REJECTED', 5), ('DRAFT', 10)]
PESU_MUN = {'DIL': 10, 'LIQ': 6, 'BAU': 5, 'MAN': 4, 'ERM': 3, 'BOB': 3, 'COV': 2, 'VIQ': 2, 'AIN': 2, 'MNF': 1, 'LAU': 1, 'AIL': 1, 'OEC': 1, 'ATA': 1}


class Command(BaseCommand):
	help = "Kria kazu DEMO (fiktísiu) ba formasaun no test. La'o iha DEBUG deit. Labele uza iha production."

	def add_arguments(self, parser):
		parser.add_argument('--total', type=int, default=80)
		parser.add_argument('--hamoos', action='store_true', help="Hamoos dadus demo antigu uluk")

	@transaction.atomic
	def handle(self, *args, **opt):
		if not settings.DEBUG:
			raise CommandError('Dadus demo permite deit iha DEBUG=True.')
		rnd = random.Random(2026)
		if opt['hamoos']:
			Kazu.objects.filter(titulu__startswith='[DEMO]').delete()
		invs = []
		for m in Munisipiu.objects.all():
			email = f'demo.{m.code.lower()}@smkre.demo'
			u, created = User.objects.get_or_create(username=email, defaults={'email': email})
			if created:
				u.set_unusable_password(); u.save()
				u.groups.add(Group.objects.get_or_create(name=INVESTIGADOR)[0])
				p = Pesoal.objects.create(name=f'Investigadór Demo {m.name}', email=email, sexo=rnd.choice(['Mane', 'Feto']), munisipiu=m)
				PesoalUser.objects.create(pesoal=p, user=u, must_change_password=False)
			invs.append((m, u))
		tipus, rais, eviks, ators = list(TipuKonflitu.objects.exclude(code='SELUK')), list(TipuRai.objects.all()), list(TipuEviksaun.objects.all()), list(TipuAtor.objects.all())
		nes, est = list(NesesidadeUrjente.objects.all()), list(EstraguPatrimoniu.objects.all())
		pesu_m = [PESU_MUN.get(m.code, 1) for m, _u in invs]
		hoje = timezone.localdate()
		for i in range(opt['total']):
			m, u = rnd.choices(invs, weights=pesu_m)[0]
			status = rnd.choices([s for s, _w in STATUS_PESU], weights=[w for _s, w in STATUS_PESU])[0]
			dr = hoje - timedelta(days=rnd.randint(0, 360))
			k = Kazu.objects.create(
				titulu=f'[DEMO] Kazu {i + 1:03d}', status=status, munisipiu=m, created_by=u,
				data_relatoriu=dr, data_akontesimentu=dr - timedelta(days=rnd.randint(0, 20)),
				latitude=Decimal(str(round(float(m.latitude or -8.8) + rnd.uniform(-0.07, 0.07), 6))),
				longitude=Decimal(str(round(float(m.longitude or 125.8) + rnd.uniform(-0.09, 0.09), 6))),
				gps_akurasia=rnd.randint(5, 40), tipu_rai=rnd.choice(rais), konsentimentu=True,
				deskrisaun="Dadus DEMO fiktísiu ba formasaun. La'ós kazu loloos.",
				status_kazu=rnd.choice(['ABERTU', 'INVESTIGASAUN', 'AKSAUN_LEGAL']) if status in ('VERIFIED', 'APPROVED') else ('TAKA' if status == 'COMPLETED' else 'ABERTU'))
			k.tipu_konflitu.set(rnd.sample(tipus, rnd.choice([1, 1, 2])))
			k.estragu.set(rnd.sample(est, rnd.randint(0, 2)))
			if rnd.random() < 0.25:
				k.nesesidade.set(rnd.sample(nes, rnd.randint(1, 2)))
				k.urjente = True
			if status != 'DRAFT':
				k.kode = generate_kode(k)
				k.synced_at = timezone.now()
			k.save()
			mane, feto = rnd.randint(3, 60), rnd.randint(3, 60)
			UmaKainAfetada.objects.create(kazu=k, uma_kain=rnd.randint(1, 30), total_ema=mane + feto, mane=mane, feto=feto,
				labarik=rnd.randint(0, (mane + feto) // 2), katuas_ferik=rnd.randint(0, 10), defisiensia=rnd.randint(0, 3))
			if any(t.code == 'DESLOKAMENTU' for t in k.tipu_konflitu.all()):
				InsidenteEviksaun.objects.create(kazu=k, tipu_eviksaun=rnd.choice(eviks), loron_avizu=rnd.randint(0, 30), forsa_seguransa=rnd.random() < 0.5)
			AtorEnvolvidu.objects.create(kazu=k, tipu_ator=rnd.choice(ators))
			KazuHistoria.objects.create(kazu=k, user=u, tipu=KazuHistoria.EDITA, status_foun=status, nota='KRIA')
		self.stdout.write(self.style.SUCCESS(f'Kazu DEMO kria ona: {opt["total"]}. Hamoos ho --hamoos.'))
