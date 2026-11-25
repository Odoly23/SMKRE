"""Teste papél Sekretariadu: input kazu (online + offline) + aprova bainhira Superadmin la iha."""
from django.core.cache import cache
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

	def test_bele_aprova_kazu_rasik(self):
		k = self.kazu(self.sek)
		self.assertIn('aprova', available_actions(self.sek, k))
		change_status(k, self.sek, 'aprova')
		k.refresh_from_db()
		self.assertEqual(k.status, 'APPROVED')

	def test_bele_verifika(self):
		k = self.kazu(self.inv, status='SYNCED')
		self.assertIn('verifika', available_actions(self.sek, k))

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
		self.kazu(self.sek, kode='RASIK')                       # kazu rasik mós tama iha "hein"
		self.client.force_login(self.sek)
		r = self.client.get(reverse('home'))
		self.assertEqual(r.context['tot_hein'], 13)
		self.assertEqual(len(r.context['objects']), 10)
		r2 = self.client.get(reverse('home') + '?page=2')
		self.assertEqual(len(r2.context['objects']), 3)

	def test_api_legal_offline_permite(self):
		token = str(RefreshToken.for_user(self.sek).access_token)
		r = self.client.get(reverse('api-sinkron-legal-opsaun'), HTTP_AUTHORIZATION=f'Bearer {token}')
		self.assertEqual(r.status_code, 200)
		self.assertTrue(r.json()['legal'])

	def test_input_legal_online_ho_autorizasaun(self):
		from datetime import timedelta
		from users.models import OfflinePermission
		self.client.force_login(self.sek)
		self.assertEqual(self.client.get(reverse('legal-survei-add')).status_code, 200)      # Sekretariadu: la presiza autorizasaun
		OfflinePermission.objects.create(user=self.sek, start_date=timezone.now() - timedelta(hours=1),
			end_date=timezone.now() + timedelta(days=5), given_by=self.adm)
		self.assertEqual(self.client.get(reverse('legal-survei-add')).status_code, 200)


class SekretariaduMunisipiuHotuTest(TestCase):
	# Sekretariadu la iha munisípiu knaar: input ba munisípiu HOTU (Investigadór de'it mak hili knaar)
	def setUp(self):
		cache.clear()
		setup_master()
		self.sek = make_user(SEKRETARIADU, munisipiu_code='XXX')       # la iha munisípiu

	def test_formulariu_web_munisipiu_hotu(self):
		self.client.force_login(self.sek)
		r = self.client.get(reverse('kazu-add'))
		self.assertEqual(r.status_code, 200)
		self.assertEqual(r.context['form'].fields['munisipiu'].queryset.count(), Munisipiu.active.count())

	def test_app_offline_munisipiu_hotu(self):
		token = str(RefreshToken.for_user(self.sek).access_token)
		r = self.client.get(reverse('api-sinkron-opsaun'), HTTP_AUTHORIZATION=f'Bearer {token}')
		self.assertEqual(r.status_code, 200)
		self.assertEqual(len(r.json()['munisipiu_lista']), Munisipiu.active.count())

	def test_investigador_sein_munisipiu_labele(self):
		inv = make_user(INVESTIGADOR, email='inv2@teste.tl', munisipiu_code='XXX')
		self.client.force_login(inv)
		self.assertRedirects(self.client.get(reverse('kazu-add')), reverse('kazu-list'), fetch_redirect_response=False)

	def test_input_legal_munisipiu_hotu(self):
		from legal.forms import SurveiLegalForm
		self.assertEqual(SurveiLegalForm().fields['munisipiu'].queryset.count(), Munisipiu.active.count())
		token = str(RefreshToken.for_user(self.sek).access_token)
		r = self.client.get(reverse('api-sinkron-legal-opsaun'), HTTP_AUTHORIZATION=f'Bearer {token}')
		self.assertEqual(len(r.json()['munisipiu_lista']), Munisipiu.active.count())


class EmailFallaTest(TestCase):
	# SMTP falla iha modu eager → pájina la sai erru 500 (Retry), email rejista de'it iha log
	def test_email_falla_la_halo_erru(self):
		from unittest import mock
		from config.tasks import send_email_task
		with mock.patch('config.tasks.send_html_email', return_value=False):
			self.assertFalse(send_email_task.delay('S', 'x.html', {}, ['a@b.tl']).get())


class SekretariaduHotuTest(TestCase):
	# Sekretariadu: verifika, fó autorizasaun offline, input legál la ho autorizasaun, edita kazu hotu
	def setUp(self):
		cache.clear()
		setup_master()
		self.sek = make_user(SEKRETARIADU, munisipiu_code='XXX')
		self.inv = make_user(INVESTIGADOR)
		self.liq = Munisipiu.objects.get(code='LIQ')

	def test_verifika_no_aprova(self):
		k = Kazu.objects.create(munisipiu=self.liq, status='SYNCED', created_by=self.inv, kode='H-1', synced_at=timezone.now())
		change_status(k, self.sek, 'verifika')
		change_status(k, self.sek, 'aprova')
		k.refresh_from_db()
		self.assertEqual(k.status, 'APPROVED')

	def test_fo_autorizasaun_offline(self):
		self.client.force_login(self.sek)
		self.assertEqual(self.client.get(reverse('offline-list')).status_code, 200)
		self.assertEqual(self.client.get(reverse('legal-autorizasaun')).status_code, 200)

	def test_input_legal_la_ho_autorizasaun(self):
		from legal.survei import input_ativu
		self.assertTrue(input_ativu(self.sek))
		self.client.force_login(self.sek)
		self.assertEqual(self.client.get(reverse('legal-survei-add')).status_code, 200)

	def test_app_offline_la_ho_autorizasaun(self):
		from users.api.views import _offline_info
		self.assertTrue(_offline_info(self.sek)['offline_ativu'])

	def test_edita_kazu_ema_seluk(self):
		from kazu.permissions import can_edit
		k = Kazu.objects.create(munisipiu=self.liq, status='VERIFIED', created_by=self.inv, kode='H-2')
		self.assertTrue(can_edit(self.sek, k))
		self.client.force_login(self.sek)
		r = self.client.get(reverse('kazu-update', args=[k.pk]))
		self.assertEqual(r.status_code, 200)
		self.assertFalse(r.context['pode_haruka'])            # la'ós kazu rasik: rai de'it, status la muda
		k.status = 'CANCELED'; k.save()
		self.assertFalse(can_edit(self.sek, k))
