"""Teste: lista kazu ba imprime (advokasia) + Sekretariadu import / export."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from config.rbac import SEKRETARIADU, INVESTIGADOR, ANALISTA
from config.testing import setup_master, make_user
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import Kazu, UmaKainAfetada


class ImprimeTest(TestCase):
	def setUp(self):
		setup_master()
		self.sek = make_user(SEKRETARIADU, munisipiu_code='XXX')
		self.inv = make_user(INVESTIGADOR)
		liq, dil = Munisipiu.objects.get(code='LIQ'), Munisipiu.objects.get(code='DIL')
		for i, m in enumerate([liq, liq, dil]):
			k = Kazu.objects.create(munisipiu=m, status='APPROVED', created_by=self.inv, kode=f'IMP-{i}',
				titulu=f'Kazu {i}', deskrisaun='Komunidade hetan avizu.', data_relatoriu=timezone.localdate())
			k.tipu_konflitu.set([TipuKonflitu.objects.get(code='GOV-RAI-ESTADU')])
			UmaKainAfetada.objects.create(kazu=k, uma_kain=4, total_ema=10)
		self.liq = liq

	def test_imprime_ho_filtru_no_total(self):
		self.client.force_login(self.sek)
		r = self.client.get(reverse('report-imprime'), {'munisipiu': self.liq.pk})
		self.assertEqual(r.status_code, 200)
		self.assertContains(r, 'IMP-0')
		self.assertNotContains(r, 'IMP-2')                      # Dili la tama
		self.assertEqual(r.context['tot_uma'], 8)
		self.assertContains(r, 'imprime.js')

	def test_investigador_labele(self):
		self.client.force_login(self.inv)
		self.assertEqual(self.client.get(reverse('report-imprime')).status_code, 403)

	def test_buka_q_iha_imprime(self):
		self.client.force_login(self.sek)
		r = self.client.get(reverse('report-imprime'), {'q': 'IMP-2'})
		self.assertEqual(r.context['total'], 1)

	def test_sekretariadu_import_no_excel_kompletu(self):
		self.client.force_login(self.sek)
		self.assertEqual(self.client.get(reverse('kazu-import')).status_code, 200)
		r = self.client.get(reverse('kazu-list'))
		self.assertContains(r, reverse('report-imprime'))
		self.assertContains(r, reverse('kazu-import'))
		self.assertEqual(self.client.get(reverse('report-export-excel')).status_code, 200)

	def test_analista_la_iha_import(self):
		self.client.force_login(make_user(ANALISTA))
		self.assertEqual(self.client.get(reverse('kazu-import')).status_code, 403)
