"""Teste hamoos permanente (Superadmin de'it)."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from config.rbac import SUPERADMIN, ADMIN, INVESTIGADOR
from config.testing import setup_master, make_user
from custom.models import Munisipiu
from kazu.models import Kazu, KazuHistoria
from legal.models import NotaLegal
from users.models import Pesoal


class HamoosTest(TestCase):
	def setUp(self):
		setup_master()
		self.sa = make_user(SUPERADMIN, email='sa@teste.tl')
		self.adm = make_user(ADMIN)
		self.inv = make_user(INVESTIGADOR)
		self.liq = Munisipiu.objects.get(code='LIQ')

	def kazu(self):
		k = Kazu.objects.create(munisipiu=self.liq, status='SYNCED', created_by=self.inv, kode='H-1', synced_at=timezone.now())
		KazuHistoria.objects.create(kazu=k, user=self.inv, status_antes='DRAFT', status_foun='SYNCED')
		return k

	def url(self, tipu, pk):
		return reverse('hamoos', args=[tipu, pk])

	def test_admin_labele(self):
		k = self.kazu()
		self.client.force_login(self.adm)
		self.assertEqual(self.client.post(self.url('kazu', k.pk)).status_code, 403)
		self.assertTrue(Kazu.objects.filter(pk=k.pk).exists())

	def test_get_la_hamoos(self):
		k = self.kazu()
		self.client.force_login(self.sa)
		self.assertEqual(self.client.get(self.url('kazu', k.pk)).status_code, 405)
		self.assertTrue(Kazu.objects.filter(pk=k.pk).exists())

	def test_superadmin_hamoos_kazu_ho_nota_legal(self):
		k = self.kazu()
		NotaLegal.objects.create(kazu=k, tipu=NotaLegal.TIPU_CHOICES[0][0], testu='Nota', created_by=self.sa)
		self.client.force_login(self.sa)
		r = self.client.post(self.url('kazu', k.pk))
		self.assertRedirects(r, reverse('kazu-list'), fetch_redirect_response=False)
		self.assertFalse(Kazu.objects.filter(pk=k.pk).exists())
		self.assertFalse(NotaLegal.objects.exists())

	def test_hamoos_utilizador_sein_dadus(self):
		adm2 = make_user(ADMIN, email='adm2@teste.tl')
		p = adm2.pesoaluser.pesoal
		self.client.force_login(self.sa)
		self.client.post(self.url('utilizador', p.uuid))
		self.assertFalse(User.objects.filter(pk=adm2.pk).exists())
		self.assertFalse(Pesoal.objects.filter(pk=p.pk).exists())

	def test_utilizador_ho_kazu_labele_hamoos(self):
		self.kazu()
		p = self.inv.pesoaluser.pesoal
		self.client.force_login(self.sa)
		r = self.client.post(self.url('utilizador', p.uuid), follow=True)
		self.assertTrue(User.objects.filter(pk=self.inv.pk).exists())
		self.assertContains(r, 'HAPARA')

	def test_labele_hamoos_an_rasik(self):
		self.client.force_login(self.sa)
		self.client.post(self.url('utilizador', self.sa.pesoaluser.pesoal.uuid))
		self.assertTrue(User.objects.filter(pk=self.sa.pk).exists())

	def test_butaun_superadmin_deit(self):
		k = self.kazu()
		self.client.force_login(self.sa)
		self.assertContains(self.client.get(reverse('kazu-detail', args=[k.pk])), self.url('kazu', k.pk))
		self.client.force_login(self.adm)
		self.assertNotContains(self.client.get(reverse('kazu-detail', args=[k.pk])), self.url('kazu', k.pk))
