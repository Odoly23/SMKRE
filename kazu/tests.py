import io
import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from config.rbac import ADMIN, SUPERADMIN, INVESTIGADOR, ANALISTA, OFISIAL_LEGAL
from config.testing import setup_master, make_user
from custom.models import Munisipiu, PostuAdministrativu, Suku, TipuKonflitu, NesesidadeUrjente, TipuAtor
from kazu.models import Kazu, Evidensia, KazuHistoria
from notification.models import Notification

MEDIA = tempfile.mkdtemp()


def jpg_bytes():
	buf = io.BytesIO()
	Image.new('RGB', (3000, 2000), (120, 160, 90)).save(buf, 'JPEG')
	return buf.getvalue()


@override_settings(MEDIA_ROOT=MEDIA)
class KazuBase(TestCase):
	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		shutil.rmtree(MEDIA, ignore_errors=True)

	def setUp(self):
		setup_master()
		self.liq = Munisipiu.objects.get(code='LIQ')
		self.postu = PostuAdministrativu.objects.get(code='LIQ-03')
		self.suku = Suku.objects.create(code='LIQ-03-01', name='Vatuvou', postu=self.postu)
		self.inv = make_user(INVESTIGADOR, email='maria@teste.tl', munisipiu_code='LIQ')
		self.admin = make_user(ADMIN)
		self.sa = make_user(SUPERADMIN)

	def form_data(self, aksaun='rai', **extra):
		data = {
			'titulu': 'Eviksaun Maubara', 'data_relatoriu': timezone.localdate().isoformat(),
			'munisipiu': self.liq.pk, 'postu': self.postu.pk, 'suku': self.suku.pk, 'aldeia': '',
			'latitude': '-8.612100', 'longitude': '125.210700', 'gps_akurasia': '12',
			'data_akontesimentu': timezone.localdate().isoformat(),
			'tipu_konflitu': [TipuKonflitu.objects.get(code='DESLOKAMENTU').pk],
			'deskrisaun': 'Familia 15 hetan avizu atu sai.', 'konsentimentu': 'on',
			'nesesidade': [NesesidadeUrjente.objects.get(code='APOIU-LEGAL').pk],
			'aksaun': aksaun,
		}
		for prefix, total in (('afetadu', 1), ('insidente', 1), ('ator', 2)):
			data.update({f'{prefix}-TOTAL_FORMS': total, f'{prefix}-INITIAL_FORMS': 0, f'{prefix}-MIN_NUM_FORMS': 0, f'{prefix}-MAX_NUM_FORMS': 20})
		data.update({'afetadu-0-uma_kain': 15, 'afetadu-0-total_ema': 72, 'afetadu-0-mane': 34, 'afetadu-0-feto': 38})
		data.update({'ator-0-tipu_ator': TipuAtor.objects.get(code='POLISIA').pk, 'ator-0-naran': 'PNTL'})
		data.update(extra)
		return data

	def post(self, url, data=None):
		# Notifikasaun haruka iha transaction.on_commit → tenke ezekuta iha test
		with self.captureOnCommitCallbacks(execute=True):
			return self.client.post(url, data or {})

	def create_kazu(self, aksaun='rai', **extra):
		self.client.force_login(self.inv)
		self.post(reverse('kazu-add'), self.form_data(aksaun, **extra))
		return Kazu.objects.latest('created_at')


class KazuFormTest(KazuBase):
	def test_rai_rascunho(self):
		kazu = self.create_kazu('rai')
		self.assertEqual(kazu.status, 'DRAFT')
		self.assertIsNone(kazu.kode)
		self.assertTrue(kazu.urjente)
		self.assertEqual(kazu.afetadu.get().total_ema, 72)
		self.assertEqual(kazu.ator.count(), 1)

	def test_munisipiu_knaar_la_bele_manipula(self):
		dil = Munisipiu.objects.get(code='DIL')
		kazu = self.create_kazu('rai', munisipiu=dil.pk)
		self.assertEqual(kazu.munisipiu, self.liq)

	def test_gps_liu_territoriu_no_akurasia(self):
		self.client.force_login(self.inv)
		r = self.client.post(reverse('kazu-add'), self.form_data(latitude='-6.2', longitude='106.8'))
		self.assertContains(r, 'territóriu Timor-Leste')
		r = self.client.post(reverse('kazu-add'), self.form_data(gps_akurasia='120'))
		self.assertContains(r, '50 m')
		self.assertEqual(Kazu.objects.count(), 0)

	def test_data_akontesimentu_labele_liu_relatoriu(self):
		self.client.force_login(self.inv)
		r = self.client.post(reverse('kazu-add'), self.form_data(data_relatoriu='2026-01-01', data_akontesimentu='2026-02-01'))
		self.assertEqual(r.status_code, 200)
		self.assertEqual(Kazu.objects.count(), 0)

	def test_seluk_presiza_esplika(self):
		self.client.force_login(self.inv)
		r = self.client.post(reverse('kazu-add'), self.form_data(tipu_konflitu=[TipuKonflitu.objects.get(code='SELUK').pk]))
		self.assertContains(r, 'Seluk')
		self.assertEqual(Kazu.objects.count(), 0)

	def test_haruka_la_iha_konsentimentu(self):
		data = self.form_data('haruka')
		del data['konsentimentu']
		self.client.force_login(self.inv)
		self.client.post(reverse('kazu-add'), data)
		self.assertEqual(Kazu.objects.count(), 0)

	def test_mane_feto_tenke_hanesan_total(self):
		self.client.force_login(self.inv)
		self.client.post(reverse('kazu-add'), self.form_data(**{'afetadu-0-feto': 10}))
		self.assertEqual(Kazu.objects.count(), 0)

	def test_dropdown_pola_custom(self):
		self.client.force_login(self.inv)
		r = self.client.get(reverse('kazu-add'))
		self.assertContains(r, 'data-posts-url="/custom/ajax/load-posts/"')
		self.assertContains(r, 'nonce=')


class WorkflowTest(KazuBase):
	def test_fluxu_kompletu_verifika_admin_aprova_superadmin(self):
		kazu = self.create_kazu('haruka')
		self.assertEqual(kazu.status, 'SYNCED')
		self.assertTrue(kazu.kode.startswith(f'SMKRE-LIQ-{timezone.localdate().year}-'))
		# Notifikasaun + email ba Admin no Superadmin (urjente)
		self.assertEqual(Notification.objects.filter(tipu='KAZU_FOUN').count(), 2)
		self.assertTrue(Notification.objects.filter(recipient=self.admin, is_urgent=True).exists())

		# Investigadór labele edita tan
		r = self.client.get(reverse('kazu-update', args=[kazu.pk]))
		self.assertRedirects(r, reverse('kazu-detail', args=[kazu.pk]))

		# Superadmin labele verifika (nivel 1 ba Admin)
		self.client.force_login(self.sa)
		self.assertEqual(self.post(reverse('kazu-action', args=[kazu.pk, 'verifika'])).status_code, 403)

		# Admin: Verifika
		self.client.force_login(self.admin)
		r = self.client.get(reverse('kazu-detail', args=[kazu.pk]))
		self.assertContains(r, 'data-target="#modal-verifika"')
		self.assertNotContains(r, 'data-target="#modal-aprova"')
		self.post(reverse('kazu-action', args=[kazu.pk, 'verifika']))
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'VERIFIED')
		self.assertEqual(kazu.verified_by, self.admin)
		self.assertTrue(Notification.objects.filter(recipient=self.sa, message__contains='aprovasaun').exists())

		# Admin labele aprova
		self.assertEqual(self.post(reverse('kazu-action', args=[kazu.pk, 'aprova'])).status_code, 403)

		# Superadmin: Aprova
		self.client.force_login(self.sa)
		self.post(reverse('kazu-action', args=[kazu.pk, 'aprova']))
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'APPROVED')
		self.assertEqual(kazu.approved_by, self.sa)

		# Remata
		self.post(reverse('kazu-action', args=[kazu.pk, 'remata']))
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'COMPLETED')
		self.assertEqual(kazu.historia.filter(tipu=KazuHistoria.DADUS).count(), 4)
		self.assertTrue(Notification.objects.filter(recipient=self.inv, tipu='KAZU_STATUS').count() >= 3)

	def test_rejeita_presiza_razaun_depois_hadia_haruka_fali(self):
		kazu = self.create_kazu('haruka')
		kode = kazu.kode
		self.client.force_login(self.admin)
		self.post(reverse('kazu-action', args=[kazu.pk, 'rejeita']), {'nota': ''})
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'SYNCED')
		self.post(reverse('kazu-action', args=[kazu.pk, 'rejeita']), {'nota': 'Atór envolvidu la kompletu'})
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'REJECTED')
		n = Notification.objects.get(recipient=self.inv, tipu='KAZU_STATUS')
		self.assertIn('Atór envolvidu la kompletu', n.message)
		self.assertTrue(n.is_urgent)

		# Investigadór hadia no haruka fali → kódigu hanesan
		self.client.force_login(self.inv)
		self.assertEqual(self.client.get(reverse('kazu-update', args=[kazu.pk])).status_code, 200)
		self.post(reverse('kazu-submit', args=[kazu.pk]))
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'SYNCED')
		self.assertEqual(kazu.kode, kode)

	def test_kansela_final(self):
		kazu = self.create_kazu('haruka')
		self.client.force_login(self.sa)
		self.post(reverse('kazu-action', args=[kazu.pk, 'kansela']), {'nota': 'Duplikadu ho kazu seluk'})
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'CANCELED')
		self.post(reverse('kazu-action', args=[kazu.pk, 'verifika']))
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'CANCELED')
		self.client.force_login(self.inv)
		self.assertEqual(self.post(reverse('kazu-submit', args=[kazu.pk])).status_code, 302)
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'CANCELED')

	def test_butaun_tuir_status(self):
		# Regra butaun: Aprova xave to'o verifika · Rejeita/Kansela xave hafoin verifika ·
		# Rejeitadu: Verifika xave to'o haruka fali · Kanseladu: hotu xave
		from kazu.services import available_actions
		kazu = self.create_kazu('haruka')
		self.assertEqual(available_actions(self.admin, kazu), ['verifika', 'rejeita', 'kansela'])
		self.assertEqual(available_actions(self.sa, kazu), ['rejeita', 'kansela'])     # Aprova xave

		# Superadmin haree Aprova xave ho razaun
		self.client.force_login(self.sa)
		r = self.client.get(reverse('kazu-detail', args=[kazu.pk]))
		self.assertNotContains(r, 'data-target="#modal-aprova"')
		self.assertContains(r, 'Hein Admin verifika uluk')

		# Hafoin verifika: Aprova ativu, Rejeita/Kansela xave (servidór mós bloku)
		self.client.force_login(self.admin)
		self.post(reverse('kazu-action', args=[kazu.pk, 'verifika']))
		kazu.refresh_from_db()
		self.assertEqual(available_actions(self.sa, kazu), ['aprova'])
		self.assertEqual(available_actions(self.admin, kazu), [])
		self.post(reverse('kazu-action', args=[kazu.pk, 'rejeita']), {'nota': 'Koko rejeita hafoin verifika'})
		self.client.force_login(self.sa)
		self.post(reverse('kazu-action', args=[kazu.pk, 'kansela']), {'nota': 'Koko kansela hafoin verifika'})
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'VERIFIED')

	def test_rejeitadu_verifika_xave_to_haruka_fali(self):
		from kazu.services import available_actions
		kazu = self.create_kazu('haruka')
		self.client.force_login(self.admin)
		self.post(reverse('kazu-action', args=[kazu.pk, 'rejeita']), {'nota': 'Dadus la kompletu'})
		kazu.refresh_from_db()
		self.assertEqual(available_actions(self.admin, kazu), ['kansela'])
		r = self.client.get(reverse('kazu-detail', args=[kazu.pk]))
		self.assertNotContains(r, 'data-target="#modal-verifika"')
		self.assertContains(r, 'Hein Investigadór hadia no haruka fali')
		self.post(reverse('kazu-action', args=[kazu.pk, 'verifika']))
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'REJECTED')

		# Investigadór haruka fali → Verifika loke fali
		self.client.force_login(self.inv)
		self.post(reverse('kazu-submit', args=[kazu.pk]))
		kazu.refresh_from_db()
		self.assertEqual(available_actions(self.admin, kazu), ['verifika', 'rejeita', 'kansela'])

	def test_kanseladu_butaun_hotu_xave(self):
		from kazu.services import action_buttons
		kazu = self.create_kazu('haruka')
		self.client.force_login(self.admin)
		self.post(reverse('kazu-action', args=[kazu.pk, 'kansela']), {'nota': 'Duplikadu ho kazu seluk'})
		kazu.refresh_from_db()
		for user in (self.admin, self.sa):
			self.assertTrue(all(not b['ativu'] for b in action_buttons(user, kazu)))
		r = self.client.get(reverse('kazu-detail', args=[kazu.pk]))
		self.assertNotContains(r, "data-toggle=\"modal\"")
		self.assertContains(r, 'Kazu kanseladu')

	def test_la_publika_iha_formulariu(self):
		kazu = self.create_kazu('rai', la_publika='on')
		self.assertTrue(kazu.la_publika)

	def test_kodigu_la_bentrok(self):
		k1 = self.create_kazu('haruka')
		k2 = self.create_kazu('haruka')
		self.assertNotEqual(k1.kode, k2.kode)
		self.assertTrue(k2.kode.endswith('00002'))

	def test_status_kazu_ofisial_legal(self):
		kazu = self.create_kazu('haruka')
		legal = make_user(OFISIAL_LEGAL)
		self.client.force_login(legal)
		self.post(reverse('kazu-status-kazu', args=[kazu.pk]), {'status_kazu': 'AKSAUN_LEGAL'})
		kazu.refresh_from_db()
		self.assertEqual(kazu.status_kazu, 'ABERTU')        # seidauk verifika
		self.client.force_login(self.admin)
		self.post(reverse('kazu-action', args=[kazu.pk, 'verifika']))
		self.client.force_login(legal)
		self.post(reverse('kazu-status-kazu', args=[kazu.pk]), {'status_kazu': 'AKSAUN_LEGAL', 'nota': 'Tribunál Distritál'})
		kazu.refresh_from_db()
		self.assertEqual(kazu.status_kazu, 'AKSAUN_LEGAL')


class AccessTest(KazuBase):
	def test_investigador_seluk_labele_haree(self):
		kazu = self.create_kazu('rai')
		outro = make_user(INVESTIGADOR, email='joao@teste.tl')
		self.client.force_login(outro)
		self.assertEqual(self.client.get(reverse('kazu-detail', args=[kazu.pk])).status_code, 404)
		self.assertEqual(self.client.get(reverse('kazu-update', args=[kazu.pk])).status_code, 403)
		self.assertNotContains(self.client.get(reverse('kazu-list')), str(kazu))

	def test_analista_haree_maibe_labele_aksaun(self):
		kazu = self.create_kazu('haruka')
		self.client.force_login(make_user(ANALISTA))
		r = self.client.get(reverse('kazu-detail', args=[kazu.pk]))
		self.assertEqual(r.status_code, 200)
		self.assertNotContains(r, "data-toggle=\"modal\"")
		self.assertEqual(self.post(reverse('kazu-action', args=[kazu.pk, 'verifika'])).status_code, 403)

	def test_admin_labele_kria_kazu(self):
		self.client.force_login(self.admin)
		self.assertEqual(self.client.get(reverse('kazu-add')).status_code, 403)

	def test_aksaun_tenke_post(self):
		kazu = self.create_kazu('haruka')
		self.client.force_login(self.admin)
		self.assertEqual(self.client.get(reverse('kazu-action', args=[kazu.pk, 'verifika'])).status_code, 405)


class EvidensiaTest(KazuBase):
	def test_foto_kompresa_limite_no_media_protegidu(self):
		kazu = self.create_kazu('rai')
		url = reverse('kazu-evidensia', args=[kazu.pk])
		for i in range(5):
			r = self.client.post(url, {'tipu': 'FOTO', 'file': SimpleUploadedFile(f'f{i}.jpg', jpg_bytes(), 'image/jpeg')})
			self.assertEqual(r.status_code, 302)
		self.assertEqual(kazu.foto_count(), 5)
		foto = kazu.evidensia.first()
		with Image.open(foto.file.path) as img:
			self.assertLessEqual(max(img.size), 1600)
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'ONGOING')        # GPS + foto → Iha Terrenu
		r = self.client.post(url, {'tipu': 'FOTO', 'file': SimpleUploadedFile('f6.jpg', jpg_bytes(), 'image/jpeg')})
		self.assertContains(r, 'máximu 5')

		# Media: dono bele loke; investigadór seluk labele; la login → login
		self.assertEqual(self.client.get(foto.file.url).status_code, 200)
		self.client.force_login(make_user(INVESTIGADOR, email='joao@teste.tl'))
		self.assertEqual(self.client.get(foto.file.url).status_code, 404)
		self.client.logout()
		self.assertEqual(self.client.get(foto.file.url).status_code, 302)

	def test_formatu_la_permite(self):
		kazu = self.create_kazu('rai')
		r = self.client.post(reverse('kazu-evidensia', args=[kazu.pk]), {'tipu': 'VIDEO', 'file': SimpleUploadedFile('x.exe', b'MZ', 'application/octet-stream')})
		self.assertContains(r, 'Formatu')
		self.assertEqual(Evidensia.objects.count(), 0)


class KomanduTesteOnlineTest(KazuBase):
	def test_cek_kazu_hatudu_dalan_kazu(self):
		from io import StringIO
		from django.core.management import call_command
		kazu = self.create_kazu('haruka')
		self.client.force_login(self.admin)
		self.post(reverse('kazu-action', args=[kazu.pk, 'verifika']))
		self.client.force_login(self.sa)
		self.post(reverse('kazu-action', args=[kazu.pk, 'aprova']))
		kazu.refresh_from_db()
		out = StringIO()
		call_command('cek_kazu', '--kode', kazu.kode, stdout=out)
		linha = [l for l in out.getvalue().splitlines() if kazu.kode in l][0]
		self.assertIn('WEB', linha)
		self.assertIn('APPROVED', linha)
		self.assertTrue(linha.rstrip().endswith('SIN'))              # mosu iha portal

	@override_settings(DEBUG=False)
	def test_teste_online_labele_iha_production(self):
		from django.core.management import call_command
		from django.core.management.base import CommandError
		with self.assertRaises(CommandError):
			call_command('teste_online')

	@override_settings(DEBUG=True)
	def test_teste_online_kria_konta_tolu(self):
		from io import StringIO
		from django.core.management import call_command
		call_command('teste_online', stdout=StringIO())
		for email in ('teste.investigador@redebarai.org', 'teste.admin@redebarai.org', 'teste.superadmin@redebarai.org'):
			from django.contrib.auth.models import User
			u = User.objects.get(username=email)
			self.assertTrue(u.check_password('Teste#Online-2026') and not u.pesoaluser.must_change_password, email)


class ImportExcelTest(KazuBase):
	# Import kazu husi Excel (Admin deit) + hadia lokasaun iha mapa
	def excel(self, lina, naran='kazu.xlsx'):
		from io import BytesIO
		from openpyxl import Workbook
		from django.core.files.uploadedfile import SimpleUploadedFile
		from kazu.importa import NARAN_KOLUN
		wb = Workbook()
		ws = wb.active
		ws.title = 'Kazu'
		ws.append(NARAN_KOLUN)
		for d in lina:
			ws.append([d.get(k, '') for k in NARAN_KOLUN])
		buf = BytesIO()
		wb.save(buf)
		return SimpleUploadedFile(naran, buf.getvalue())

	def lina(self, **extra):
		d = {'data_relatoriu': timezone.localdate().isoformat(), 'munisipiu': 'LIQ', 'tipu_konflitu': 'DESLOKAMENTU',
			'deskrisaun': 'Familia hetan avizu atu sai.', 'konsentimentu': 'SIN', 'uma_kain': 4, 'mane': 6, 'feto': 7}
		d.update(extra)
		return d

	def upload(self, lina):
		self.client.force_login(self.admin)
		r = self.client.post(reverse('kazu-import'), {'file': self.excel(lina)})
		self.assertEqual(r.status_code, 302, r.content[:300])
		from kazu.models import KazuImport
		return KazuImport.objects.latest('created_at')

	def test_admin_deit(self):
		for user, kodigu in ((self.inv, 403), (self.sa, 403), (self.admin, 200)):
			self.client.force_login(user)
			self.assertEqual(self.client.get(reverse('kazu-import')).status_code, kodigu)
		r = self.client.get(reverse('kazu-import-template'))
		self.assertEqual(r.status_code, 200)
		self.assertTrue(r.content.startswith(b'PK'))

	def test_pratinjau_konfirma_no_gps_aproksimadu(self):
		imp = self.upload([
			self.lina(latitude='-8.612100', longitude='125.210700', postu='LIQ-03', suku='LIQ-03-01'),   # GPS loos
			self.lina(deskrisaun='La iha GPS'),                                                         # sentru munisípiu
			self.lina(deskrisaun='GPS la kompletu', latitude='-8.6'),                                    # la kompletu
			self.lina(deskrisaun='GPS li\'ur TL', latitude='-6.2', longitude='106.8'),                    # Jakarta
			self.lina(munisipiu='XYZ'),                                                                  # erru
			self.lina(tipu_konflitu='', deskrisaun=''),                                                  # erru
		])
		self.assertEqual((imp.total, imp.total_ok, imp.total_aproksimadu), (6, 4, 3))
		self.assertEqual(Kazu.objects.count(), 0)                     # pratinjau: seidauk kria
		r = self.client.get(reverse('kazu-import-detail', args=[imp.pk]))
		self.assertContains(r, 'XYZ')
		self.assertContains(r, 'data-target="#modal-konfirma-import"')

		self.post(reverse('kazu-import-konfirma', args=[imp.pk]))
		kazu = Kazu.objects.filter(importasaun=imp)
		self.assertEqual(kazu.count(), 4)
		self.assertTrue(all(k.status == 'SYNCED' and k.kode.startswith('SMKRE-LIQ-') for k in kazu))
		self.assertEqual(kazu.filter(gps_aproksimadu=True).count(), 3)
		loos = kazu.get(gps_aproksimadu=False)
		self.assertEqual(str(loos.latitude), '-8.612100')
		self.assertEqual(loos.afetadu.get().total_ema, 13)
		self.assertTrue(loos.historia.filter(nota__contains='Import Excel').exists())
		self.assertTrue(Notification.objects.filter(recipient=self.sa, message__contains='Excel').exists())
		# Konfirma dala rua: la kria tan
		self.post(reverse('kazu-import-konfirma', args=[imp.pk]))
		self.assertEqual(Kazu.objects.count(), 4)

	def test_la_iha_konsentimentu_la_tama_portal(self):
		imp = self.upload([self.lina(konsentimentu='')])
		self.post(reverse('kazu-import-konfirma', args=[imp.pk]))
		self.assertFalse(Kazu.objects.get().konsentimentu)

	def test_file_la_validu(self):
		from django.core.files.uploadedfile import SimpleUploadedFile
		self.client.force_login(self.admin)
		r = self.client.post(reverse('kazu-import'), {'file': SimpleUploadedFile('kazu.xlsx', b'naran,data\n1,2')})
		self.assertEqual(r.status_code, 200)
		self.assertContains(r, '.xlsx')

	def test_hadia_lokasaun(self):
		imp = self.upload([self.lina()])
		self.post(reverse('kazu-import-konfirma', args=[imp.pk]))
		kazu = Kazu.objects.get()
		self.assertTrue(kazu.gps_aproksimadu)
		url = reverse('kazu-lokasaun', args=[kazu.pk])
		self.assertContains(self.client.get(reverse('kazu-detail', args=[kazu.pk])), url)
		self.assertContains(self.client.get(url), 'mapa-pick')
		# Li'ur Timor-Leste: rejeita
		self.post(url, {'latitude': '-6.200000', 'longitude': '106.800000'})
		kazu.refresh_from_db()
		self.assertTrue(kazu.gps_aproksimadu)
		# Fatin loos
		self.post(url, {'latitude': '-8.598765', 'longitude': '125.256789'})
		kazu.refresh_from_db()
		self.assertFalse(kazu.gps_aproksimadu)
		self.assertEqual(str(kazu.longitude), '125.256789')
		self.assertTrue(kazu.historia.filter(nota__contains='Lokasaun muda').exists())
		# Investigadór labele; hafoin aprova labele muda
		self.client.force_login(self.inv)
		self.assertEqual(self.client.get(url).status_code, 403)
		Kazu.objects.filter(pk=kazu.pk).update(status='APPROVED')
		self.client.force_login(self.admin)
		self.assertRedirects(self.client.get(url), reverse('kazu-detail', args=[kazu.pk]))
