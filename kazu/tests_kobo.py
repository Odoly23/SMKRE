"""Koneksaun Kobo → Kazu: mapeamentu, dedup, dry-run, kria liuhusi pipeline import."""
from unittest import mock
from django.test import TestCase
from config.testing import setup_master, make_user
from config.rbac import ADMIN, INVESTIGADOR
from custom.models import Munisipiu, Suku, PostuAdministrativu, TipuKonflitu
from kazu.models import Kazu
from kazu import kobo


def _sub(uuid, **extra):
	# Submission Kobo ezemplu (naran pergunta tuir MAPA default)
	d = {
		'_uuid': uuid, 'data_relatoriu': '2026-10-20', 'munisipiu': 'Liquiçá', 'postu': 'Maubara',
		'suku': 'Vatuvou', 'tipu_konflitu': 'Disputa entre indivíduu ho komunidade', 'deskrisaun': 'Eviksaun iha Lebumeta',
		'gps': '-8.6121 125.5736 0 8', 'konsentimentu': 'Sin', 'uma_kain': '15', 'mane': '34', 'feto': '38',
		'titulu': 'Kazu Kobo teste',
	}
	d.update(extra)
	return d


class KoboBaseTest(TestCase):
	def setUp(self):
		setup_master()
		self.admin = make_user(ADMIN, email='adm.kobo@teste.tl')
		make_user(INVESTIGADOR, email='inv.kobo@teste.tl')
		self.liq = Munisipiu.objects.get(code='LIQ')
		postu = PostuAdministrativu.objects.get(code='LIQ-03')       # Maubara (tuir _sub)
		if not Suku.objects.filter(name__iexact='Vatuvou').exists():
			Suku.objects.create(code='LIQ-03-VV', name='Vatuvou', postu=postu)
		# tipu konflitu ho naran ne'ebé mapa uza
		self.tipu = TipuKonflitu.active.first()

	def _patch(self, subs):
		return mock.patch.object(kobo, 'buka_submissions', return_value=subs)


class MapaTest(KoboBaseTest):
	def test_kobo_ba_lina_mapeia_gps_no_konsentimentu(self):
		d = kobo.kobo_ba_lina(_sub('u1'), 1)
		self.assertEqual(d['latitude'], '-8.6121')
		self.assertEqual(d['longitude'], '125.5736')
		self.assertEqual(d['konsentimentu'], 'Sin')
		self.assertEqual(d['munisipiu'], 'Liquiçá')
		self.assertEqual(d['_kobo_uuid'], 'u1')

	def test_grupu_prefix(self):
		# Kobo dalaruma fó 'grupu/pergunta' → _kfg tenke hetan
		d = kobo.kobo_ba_lina({'_uuid': 'g1', 'grupu1/munisipiu': 'Dili'}, 1)
		self.assertEqual(d['munisipiu'], 'Dili')


class SyncTest(KoboBaseTest):
	def test_dry_run_la_kria(self):
		with self._patch([_sub('u1'), _sub('u2')]):
			r = kobo.sync(self.admin, dry_run=True)
		self.assertEqual(r['total'], 2)
		self.assertEqual(r['foun'], 2)
		self.assertEqual(r['kria'], 0)
		self.assertEqual(Kazu.objects.filter(kobo_uuid__isnull=False).count(), 0)

	def test_kria_no_dedup(self):
		with self._patch([_sub('u1'), _sub('u2')]):
			r = kobo.sync(self.admin, dry_run=False)
		self.assertEqual(r['kria'], 2, r['erru'])
		self.assertEqual(set(Kazu.objects.values_list('kobo_uuid', flat=True)) & {'u1', 'u2'}, {'u1', 'u2'})
		k = Kazu.objects.get(kobo_uuid='u1')
		self.assertEqual(k.status, 'SYNCED')                        # hein verifikasaun
		self.assertEqual(k.munisipiu, self.liq)
		self.assertEqual(str(k.latitude), '-8.612100')
		# Sync fali ho submission hanesan → la kria duplikadu
		with self._patch([_sub('u1'), _sub('u2'), _sub('u3')]):
			r2 = kobo.sync(self.admin, dry_run=False)
		self.assertEqual(r2['foun'], 1)                              # u3 de'it foun
		self.assertEqual(r2['kria'], 1)
		self.assertEqual(Kazu.objects.filter(kobo_uuid__in=['u1', 'u2', 'u3']).count(), 3)

	def test_submission_sala_konta_sala(self):
		# Munisípiu la hetan → sala (la kria), la estraga sync tomak
		with self._patch([_sub('ok1'), _sub('bad1', munisipiu='Munisipiu Falsu')]):
			r = kobo.sync(self.admin, dry_run=False)
		self.assertEqual(r['kria'], 1)
		self.assertEqual(r['sala'], 1)
		self.assertFalse(Kazu.objects.filter(kobo_uuid='bad1').exists())

	def test_config_la_kompletu_hatudu_erru(self):
		from django.test import override_settings
		with override_settings(KOBO_TOKEN='', KOBO_ASSET_UID=''):
			with self.assertRaises(RuntimeError):
				kobo._config()
