"""Teste papél Sekretariadu: input kazu (online + offline) + aprova bainhira Superadmin la iha."""
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from config.rbac import SEKRETARIADU, ADMIN, INVESTIGADOR
from config.testing import setup_master, make_user
from custom.models import Munisipiu
from kazu.models import Kazu
from kazu.services import change_status, available_actions


class SekretariaduTest(TestCase):
	def setUp(self):
		cache.clear()
		setup_master()
		self.sek = make_user(SEKRETARIADU)
		self.inv = make_user(INVESTIGADOR)
		self.adm = make_user(ADMIN)
		self.liq = Munisipiu.objects.get(code='LIQ')

	def kazu(self, user, status='VERIFIED', kode='S-1'):
		return Kazu.objects.create(munisipiu=self.liq, status=status, created_by=user, kode=kode, synced_at=timezone.now())

	def test_aprova_kazu_ema_seluk(self):
		k = self.kazu(self.inv)
		self.assertIn('aprova', available_actions(self.sek, k))
		change_status(k, self.sek, 'aprova')
		k.refresh_from_db()
		self.assertEqual((k.status, k.approved_by), ('APPROVED', self.sek))

	def test_labele_aprova_kazu_rasik(self):
		k = self.kazu(self.sek)
		self.assertNotIn('aprova', available_actions(self.sek, k))
		with self.assertRaises(ValidationError):
			change_status(k, self.sek, 'aprova')

	def test_labele_verifika(self):
		k = self.kazu(self.inv, status='SYNCED')
		self.assertNotIn('verifika', available_actions(self.sek, k))

	def test_input_online_no_haree_kazu_hotu(self):
		self.client.force_login(self.sek)
		self.assertEqual(self.client.get(reverse('kazu-add')).status_code, 200)
		self.kazu(self.inv)
		self.assertContains(self.client.get(reverse('kazu-list')), 'S-1')

	def test_api_offline_permite(self):
		token = str(RefreshToken.for_user(self.sek).access_token)
		r = self.client.get(reverse('api-sinkron-opsaun'), HTTP_AUTHORIZATION=f'Bearer {token}')
		self.assertEqual(r.status_code, 200)

	def test_varanda_hein_aprova_pajina_10(self):
		for i in range(12):
			self.kazu(self.inv, kode=f'V-{i:02d}')
		self.kazu(self.sek, kode='RASIK')                       # kazu rasik la tama iha "hein"
		self.client.force_login(self.sek)
		r = self.client.get(reverse('home'))
		self.assertEqual(r.context['tot_hein'], 12)
		self.assertEqual(len(r.context['objects']), 10)
		r2 = self.client.get(reverse('home') + '?page=2')
		self.assertEqual(len(r2.context['objects']), 2)
		self.assertNotContains(r2, 'RASIK')
