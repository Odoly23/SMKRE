"""Limpeza automátiku (kazu/limpeza.py): loron 30 la verifika / la aprova → kansela; loron 30 tan → hamoos."""
import os
import shutil
import tempfile
from datetime import timedelta
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from config.rbac import ADMIN, SUPERADMIN, INVESTIGADOR
from config.testing import setup_master, make_user
from custom.models import Munisipiu
from kazu.limpeza import hala_o, LORON
from kazu.models import Kazu, KazuImport, KazuHistoria, Evidensia
from legal.models import NotaLegal
from notification.models import Notification

MEDIA = tempfile.mkdtemp()


@override_settings(LIMPEZA_HAHU='2020-01-01', LIMPEZA_ATIVU=True, MEDIA_ROOT=MEDIA)
class LimpezaTest(TestCase):
	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		shutil.rmtree(MEDIA, ignore_errors=True)

	def setUp(self):
		setup_master()
		self.inv = make_user(INVESTIGADOR)
		self.admin = make_user(ADMIN)
		self.sa = make_user(SUPERADMIN)
		self.mun = Munisipiu.objects.get(code='LIQ')
		self.agora = timezone.now()
		self.n = 0

	# kazu ho status no data (loron liu ba)
	def kazu(self, status, loron, **extra):
		self.n += 1
		uluk = self.agora - timedelta(days=loron)
		data = {'synced_at': uluk} if status == 'SYNCED' else {'synced_at': uluk, 'verified_at': uluk} if status == 'VERIFIED' else {}
		data.update(extra)
		return Kazu.objects.create(munisipiu=self.mun, status=status, created_by=self.inv, kode=f'L-{self.n}', konsentimentu=True, **data)

	def test_loron_30_la_verifika_ka_la_aprova_kansela(self):
		hein = self.kazu('SYNCED', 31)
		verif = self.kazu('VERIFIED', 31)
		foun = self.kazu('SYNCED', 29)
		aprova = self.kazu('APPROVED', 90)
		rejeita = self.kazu('REJECTED', 90)
		with self.captureOnCommitCallbacks(execute=True):
			rez = hala_o(self.agora)
		self.assertEqual(rez['kansela'], 2)
		for k, antes in ((hein, 'SYNCED'), (verif, 'VERIFIED')):
			k.refresh_from_db()
			self.assertEqual((k.status, k.kansela_auto_antes), ('CANCELED', antes))
			self.assertTrue(KazuHistoria.objects.filter(kazu=k, status_foun='CANCELED', nota__icontains='automátiku').exists())
		for k, st in ((foun, 'SYNCED'), (aprova, 'APPROVED'), (rejeita, 'REJECTED')):
			k.refresh_from_db()
			self.assertEqual(k.status, st)
		self.assertTrue(Notification.objects.filter(recipient=self.inv, tipu='KAZU_STATUS').exists())   # Investigadór hatene

	def test_import_no_legal_la_toka(self):
		imp = KazuImport.objects.create(naran_file='baze.xlsx', sha256='x' * 64, created_by=self.admin)
		k_imp = self.kazu('SYNCED', 90, importasaun=imp)
		k_leg = self.kazu('VERIFIED', 90)
		NotaLegal.objects.create(kazu=k_leg, tipu='ANALIZE', testu='Análize')
		hala_o(self.agora)
		k_imp.refresh_from_db(); k_leg.refresh_from_db()
		self.assertEqual((k_imp.status, k_leg.status), ('SYNCED', 'VERIFIED'))

	def test_loron_hahu_proteje_kazu_tuan(self):
		k = self.kazu('SYNCED', 200)
		with self.settings(LIMPEZA_HAHU=timezone.localdate().isoformat()):
			self.assertEqual(hala_o(self.agora)['kansela'], 0)          # loron deploy: la kansela kedas
		self.assertEqual(hala_o(self.agora)['kansela'], 1)              # loron 30 hafoin hahú → kansela
		k.refresh_from_db()
		self.assertEqual(k.status, 'CANCELED')

	def test_la_ativu_la_halo_buat_ida(self):
		self.kazu('SYNCED', 90)
		with self.settings(LIMPEZA_ATIVU=False):
			self.assertEqual(hala_o(self.agora), {'kansela': 0, 'hamoos': 0, 'lembrete': 0})

	def test_kanseladu_automatiku_loron_30_hamoos_ho_file(self):
		k = self.kazu('CANCELED', 0, kansela_auto_iha=self.agora - timedelta(days=LORON + 1), kansela_auto_antes='SYNCED')
		ev = Evidensia.objects.create(kazu=k, tipu=Evidensia.FOTO, file=ContentFile(b'jpg', name='foto.jpg'))
		path = ev.file.path
		self.assertTrue(os.path.exists(path))
		manual = self.kazu('CANCELED', 0)                               # Admin kansela manuál: la hamoos
		foun = self.kazu('CANCELED', 0, kansela_auto_iha=self.agora - timedelta(days=5), kansela_auto_antes='SYNCED')
		self.assertEqual(hala_o(self.agora)['hamoos'], 1)
		self.assertFalse(Kazu.objects.filter(pk=k.pk).exists())
		self.assertFalse(os.path.exists(path))                          # foto mós lakon
		self.assertTrue(Kazu.objects.filter(pk__in=[manual.pk, foun.pk]).count() == 2)

	def test_lembrete_loron_21_ba_admin(self):
		self.kazu('SYNCED', 21)
		self.kazu('VERIFIED', 28)
		hala_o(self.agora)
		self.assertTrue(Notification.objects.filter(recipient=self.admin, tipu='SISTEMA', message__contains='loron 9').exists())
		self.assertTrue(Notification.objects.filter(recipient=self.sa, tipu='SISTEMA', message__contains='loron 2').exists())

	def test_admin_restaura(self):
		k = self.kazu('SYNCED', 31)
		hala_o(self.agora)
		self.client.force_login(self.inv)
		self.assertEqual(self.client.post(reverse('kazu-restaura', args=[k.pk])).status_code, 403)
		self.client.force_login(self.admin)
		r = self.client.get(reverse('kazu-detail', args=[k.pk]))
		self.assertContains(r, 'Restaura kazu')
		self.client.post(reverse('kazu-restaura', args=[k.pk]))
		k.refresh_from_db()
		self.assertEqual((k.status, k.kansela_auto_iha, k.kansela_auto_antes), ('SYNCED', None, ''))
		self.assertGreater(k.synced_at, self.agora - timedelta(minutes=5))   # loron 30 hahú fali
		self.assertEqual(hala_o()['kansela'], 0)

	def test_dry_run_la_muda_buat_ida(self):
		k = self.kazu('SYNCED', 40)
		rez = hala_o(self.agora, simula=True)
		self.assertEqual(rez['kansela'], 1)
		self.assertEqual(len(rez['lista_kansela']), 1)
		k.refresh_from_db()
		self.assertEqual(k.status, 'SYNCED')
		self.assertFalse(Notification.objects.exists())
