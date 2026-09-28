import tempfile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from config.rbac import INVESTIGADOR
from config.testing import setup_master, make_user
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia, TipuKonflitu


class SetupTest(TestCase):
	def test_setup_kria_dadus_no_bele_la_o_dala_rua(self):
		setup_master()
		setup_master()
		self.assertEqual(Munisipiu.objects.count(), 14)
		self.assertEqual(PostuAdministrativu.objects.count(), 65)
		self.assertTrue(TipuKonflitu.objects.get(code='SELUK').presiza_esplika)


class WilayahTest(TestCase):
	def setUp(self):
		setup_master()
		with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='utf-8') as f:
			f.write('postu_code,suku_code,suku,aldeia_code,aldeia\n')
			f.write('LIQ-03,LIQ-03-01,Vatuvou,LIQ-03-01-01,Aldeia A\n')
			f.write('LIQ-03,LIQ-03-01,Vatuvou,LIQ-03-01-02,Aldeia B\n')
			f.write('XXX-99,XXX,Sala,,\n')
			self.csv = f.name
		call_command('import_wilayah', self.csv, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))

	def test_import_suku_aldeia(self):
		self.assertEqual(Suku.objects.count(), 1)
		self.assertEqual(Aldeia.objects.count(), 2)

	def test_dropdown_presiza_login(self):
		r = self.client.get(reverse('ajax_load_suku'), {'postu': 1})
		self.assertEqual(r.status_code, 302)

	def test_dropdown_bertingkat(self):
		self.client.force_login(make_user(INVESTIGADOR))
		postu = PostuAdministrativu.objects.get(code='LIQ-03')
		r = self.client.get(reverse('ajax_load_suku'), {'postu': postu.pk})
		self.assertContains(r, 'Vatuvou')
		r = self.client.get(reverse('ajax_load_post'), {'munisipiu': postu.munisipiu_id})
		self.assertContains(r, 'Maubara')
		r = self.client.get(reverse('ajax_load_aldeia'), {'suku': Suku.objects.get().pk})
		self.assertContains(r, 'Aldeia B')
