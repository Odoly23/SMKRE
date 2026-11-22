"""Avizu GPS la tuir munisípiu (kazu/fatin.py): avizu de'it, la bloku."""
from django.test import TestCase
from django.urls import reverse
from config.rbac import ADMIN
from config.testing import setup_master, make_user
from custom.models import Munisipiu
from kazu.fatin import avizu_munisipiu, munisipiu_gps
from kazu.models import Kazu
from sinkron.tests import SinkronBase

KANTOR_DILI = (-8.5569, 125.5603)
CRISTO_REI = (-8.5136, 125.6086)          # tasi-ibun: li'ur fronteira simplifika (~2.4 km)
AILEU_VILA = (-8.7280, 125.5660)


class FatinTest(TestCase):
	def setUp(self):
		setup_master()
		self.dil = Munisipiu.objects.get(code='DIL')
		self.ail = Munisipiu.objects.get(code='AIL')

	def test_gps_iha_munisipiu_rasik_la_avizu(self):
		self.assertEqual(avizu_munisipiu(*KANTOR_DILI, self.dil), '')
		self.assertEqual(avizu_munisipiu(*AILEU_VILA, self.ail), '')

	def test_gps_iha_munisipiu_seluk_avizu(self):
		a = avizu_munisipiu(*KANTOR_DILI, self.ail)
		self.assertIn('Dili', a)
		self.assertIn('Aileu', a)
		self.assertIn('Dili', avizu_munisipiu(*KANTOR_DILI, self.ail))
		self.assertIn('Aileu', avizu_munisipiu(*AILEU_VILA, self.dil))

	def test_tasi_ibun_la_avizu_sala(self):
		# fronteira simplifika: Cristo Rei la iha laran poligon Dili, maibé besik → la avizu
		laran, besik, _d = munisipiu_gps(*CRISTO_REI, 'DIL')
		self.assertIsNone(laran)
		self.assertEqual(besik, 'DIL')
		self.assertEqual(avizu_munisipiu(*CRISTO_REI, self.dil), '')

	def test_la_iha_gps_ka_munisipiu(self):
		self.assertEqual(avizu_munisipiu(None, None, self.dil), '')
		self.assertEqual(avizu_munisipiu(*KANTOR_DILI, None), '')

	def test_detalla_kazu_hatudu_avizu(self):
		admin = make_user(ADMIN)
		k = Kazu.objects.create(munisipiu=self.ail, status='SYNCED', created_by=admin, kode='F-1', konsentimentu=True,
			latitude=KANTOR_DILI[0], longitude=KANTOR_DILI[1])
		self.client.force_login(admin)
		r = self.client.get(reverse('kazu-detail', args=[k.pk]))
		self.assertContains(r, 'maibé kazu rejista iha Aileu')
		Kazu.objects.filter(pk=k.pk).update(munisipiu=self.dil)
		self.assertNotContains(self.client.get(reverse('kazu-detail', args=[k.pk])), 'maibé kazu rejista iha')


class FatinSinkronTest(SinkronBase):
	# app offline: kazu ho GPS iha munisípiu seluk → simu (la bloku) + avizu iha resposta
	def test_sinkron_simu_ho_avizu(self):
		r = self.send(self.payload(latitude=KANTOR_DILI[0], longitude=KANTOR_DILI[1]))
		self.assertEqual(r.status_code, 201)
		self.assertIn('Dili', r.json()['avizu_fatin'])
		self.assertIn('Liquiçá', r.json()['avizu_fatin'])
