import hashlib
import shutil
import tempfile
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from config.rbac import ADMIN, SUPERADMIN, INVESTIGADOR, ANALISTA, OFISIAL_LEGAL
from config.testing import setup_master, make_user
from custom.models import Munisipiu
from kazu.models import Kazu
from legal.models import DokumentuLegal, NotaLegal, AsesuVault
from legal.tasks import lembra_prazu
from notification.models import Notification

MEDIA = tempfile.mkdtemp()
PDF = b'%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << >>\n%%EOF\n'


def pdf(naran='karta.pdf', konteudu=PDF):
	return SimpleUploadedFile(naran, konteudu, content_type='application/pdf')


@override_settings(MEDIA_ROOT=MEDIA)
class LegalBase(TestCase):
	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		shutil.rmtree(MEDIA, ignore_errors=True)

	def setUp(self):
		setup_master()
		self.inv = make_user(INVESTIGADOR)
		self.legal = make_user(OFISIAL_LEGAL)
		self.analista = make_user(ANALISTA)
		self.admin = make_user(ADMIN)
		self.kazu = Kazu.objects.create(munisipiu=Munisipiu.objects.get(code='LIQ'), status='VERIFIED', kode='RbR-LIQ-2026-0001',
			created_by=self.inv, konsentimentu=True)
		self.draft = Kazu.objects.create(munisipiu=Munisipiu.objects.get(code='LIQ'), status='DRAFT', created_by=self.inv)

	def upload(self, user=None, kazu=None, **extra):
		self.client.force_login(user or self.legal)
		data = {'kategoria': 'KARTA', 'titulu': 'Karta reklamasaun', 'file': pdf()}
		data.update(extra)
		url = reverse('legal-kazu-dok-add', args=[(kazu or self.kazu).pk])
		return self.client.post(url, data)


class AsesuTest(LegalBase):
	def test_investigador_labele_tama(self):
		self.client.force_login(self.inv)
		for url in (reverse('legal-vault'), reverse('legal-kazu-list'), reverse('legal-kazu', args=[self.kazu.pk])):
			self.assertEqual(self.client.get(url).status_code, 403, url)

	def test_analista_haree_maibe_labele_upload(self):
		self.client.force_login(self.analista)
		self.assertEqual(self.client.get(reverse('legal-kazu', args=[self.kazu.pk])).status_code, 200)
		self.assertEqual(self.upload(user=self.analista).status_code, 403)

	def test_kazu_seidauk_verifika_labele(self):
		self.assertEqual(self.upload(kazu=self.draft).status_code, 404)

	def test_konfidensial_subar_husi_analista(self):
		self.upload(konfidensial='on')
		doc = DokumentuLegal.objects.get()
		self.client.force_login(self.analista)
		self.assertEqual(self.client.get(reverse('legal-dok-download', args=[doc.pk])).status_code, 404)
		self.assertNotContains(self.client.get(reverse('legal-vault')), 'Karta reklamasaun')


class VaultTest(LegalBase):
	def test_upload_hash_no_rejistu(self):
		r = self.upload()
		self.assertRedirects(r, reverse('legal-kazu', args=[self.kazu.pk]))
		doc = DokumentuLegal.objects.get()
		self.assertEqual(doc.sha256, hashlib.sha256(PDF).hexdigest())
		self.assertTrue(doc.file.name.startswith(f'legal/{self.kazu.pk}/'))
		self.assertNotIn('karta', doc.file.name)                     # naran orijinál la iha disku
		self.assertTrue(AsesuVault.objects.filter(dokumentu=doc, aksaun='UPLOAD', user=self.legal).exists())

	def test_file_falsu_rejeita(self):
		r = self.upload(file=pdf('virus.pdf', b'MZ\x90\x00 executavel'))
		self.assertEqual(r.status_code, 200)
		self.assertFalse(DokumentuLegal.objects.exists())
		r = self.upload(file=SimpleUploadedFile('script.exe', b'MZ\x90'))
		self.assertFalse(DokumentuLegal.objects.exists())

	def test_download_rejistu_no_media_diretu_bloke(self):
		self.upload()
		doc = DokumentuLegal.objects.get()
		r = self.client.get(reverse('legal-dok-download', args=[doc.pk]))
		self.assertEqual(r.status_code, 200)
		self.assertIn('attachment', r['Content-Disposition'])
		self.assertEqual(b''.join(r.streaming_content), PDF)
		self.assertTrue(AsesuVault.objects.filter(dokumentu=doc, aksaun='DOWNLOAD').exists())
		self.assertEqual(self.client.get('/media/' + doc.file.name).status_code, 404)   # la iha dalan seluk

	def test_versaun_no_arkivu(self):
		self.upload()
		v1 = DokumentuLegal.objects.get()
		self.client.post(reverse('legal-dok-versaun', args=[v1.pk]), {'file': pdf('karta-v2.pdf', PDF + b'%v2'), 'deskrisaun': 'Asina ona'})
		v2 = DokumentuLegal.objects.get(atual=True)
		v1.refresh_from_db()
		self.assertEqual(v2.versaun, 2)
		self.assertFalse(v1.atual)
		self.assertEqual(v2.historia_versaun(), [v2, v1])
		# Arkivu: razaun obrigatóriu
		self.client.post(reverse('legal-dok-arkivu', args=[v2.pk]), {'razaun': 'x'})
		v2.refresh_from_db()
		self.assertFalse(v2.arkivadu)
		self.client.post(reverse('legal-dok-arkivu', args=[v2.pk]), {'razaun': 'Duplikadu ho dokumentu seluk'})
		v2.refresh_from_db()
		self.assertTrue(v2.arkivadu)
		self.assertNotContains(self.client.get(reverse('legal-vault')), 'Karta reklamasaun')
		self.assertEqual(DokumentuLegal.objects.count(), 2)            # la hamoos buat ida

	def test_verifika_vault(self):
		self.upload()
		call_command('verifika_vault', stdout=open('/dev/null', 'w'))
		doc = DokumentuLegal.objects.get()
		with open(doc.file.path, 'ab') as f:
			f.write(b'muda')
		with self.assertRaises(SystemExit):
			call_command('verifika_vault', stdout=open('/dev/null', 'w'))


class NotaPrazuTest(LegalBase):
	def test_nota_no_lembrete(self):
		self.client.force_login(self.legal)
		prazu = timezone.localdate() + timedelta(days=2)
		self.client.post(reverse('legal-nota-add', args=[self.kazu.pk]), {'tipu': 'AUDIENSIA', 'testu': 'Audiénsia tribunál Dili', 'prazu': prazu.isoformat()})
		nota = NotaLegal.objects.get()
		self.assertEqual(nota.created_by, self.legal)
		self.assertEqual(lembra_prazu()['lembra'], 1)
		self.assertTrue(Notification.objects.filter(recipient=self.legal, tipu='LEGAL').exists())
		# Remata → la lembra tan
		self.client.post(reverse('legal-nota-update', args=[nota.pk]), {'tipu': 'AUDIENSIA', 'testu': nota.testu, 'prazu': prazu.isoformat(), 'remata': 'on'})
		self.assertEqual(lembra_prazu()['lembra'], 0)

	def test_status_aksaun_legal_notifika(self):
		self.client.force_login(self.admin)
		with self.captureOnCommitCallbacks(execute=True):
			self.client.post(reverse('kazu-status-kazu', args=[self.kazu.pk]), {'status_kazu': 'AKSAUN_LEGAL',
				'next': reverse('legal-kazu', args=[self.kazu.pk])})
		self.assertTrue(Notification.objects.filter(recipient=self.legal, tipu='LEGAL').exists())

	def test_next_la_seguru_la_redirect_li_ur(self):
		self.client.force_login(self.admin)
		r = self.client.post(reverse('kazu-status-kazu', args=[self.kazu.pk]), {'status_kazu': 'INVESTIGASAUN', 'next': 'https://evil.example/'})
		self.assertRedirects(r, reverse('kazu-detail', args=[self.kazu.pk]))

	def test_dossier_la_hatudu_nota_konfidensial(self):
		NotaLegal.objects.create(kazu=self.kazu, tipu='ANALIZE', testu='Estratéjia sekretu', konfidensial=True, created_by=self.legal)
		NotaLegal.objects.create(kazu=self.kazu, tipu='KONSELLU', testu='Konsellu públiku', created_by=self.legal)
		self.client.force_login(self.legal)
		r = self.client.get(reverse('legal-dossier', args=[self.kazu.pk]))
		self.assertContains(r, 'Konsellu públiku')
		self.assertNotContains(r, 'Estratéjia sekretu')


class ClientIPTest(TestCase):
	@override_settings(BEHIND_PROXY=True)
	def test_ip_ikus_husi_nginx(self):
		from config.utils import get_client_ip
		req = RequestFactory().get('/', HTTP_X_FORWARDED_FOR='1.2.3.4, 203.0.113.9', REMOTE_ADDR='')
		self.assertEqual(get_client_ip(req), '203.0.113.9')          # 1.2.3.4 bele falsu

	@override_settings(BEHIND_PROXY=True, CLIENT_IP_HEADER='HTTP_X_REAL_IP')
	def test_header_pythonanywhere(self):
		from config.utils import get_client_ip
		req = RequestFactory().get('/', HTTP_X_REAL_IP='198.51.100.4', HTTP_X_FORWARDED_FOR='1.2.3.4', REMOTE_ADDR='10.0.0.2')
		self.assertEqual(get_client_ip(req), '198.51.100.4')

	@override_settings(BEHIND_PROXY=False)
	def test_la_iha_proxy(self):
		from config.utils import get_client_ip
		req = RequestFactory().get('/', HTTP_X_FORWARDED_FOR='1.2.3.4', REMOTE_ADDR='10.0.0.5')
		self.assertEqual(get_client_ip(req), '10.0.0.5')


# ══ Survei legál (Perguntas Xave Sira Legal) ══
import json as _json
import uuid as _uuid
from rest_framework_simplejwt.tokens import RefreshToken
from legal.models import SurveiLegal
from users.models import OfflinePermission
from users.services import give_offline

JPG = b'\xff\xd8\xff\xe0' + b'0' * 200


class SurveiBase(LegalBase):
	def setUp(self):
		super().setUp()
		self.mun = Munisipiu.objects.get(code='LIQ')

	def dadus(self, **extra):
		d = {'data_survei': str(timezone.localdate()), 'munisipiu': self.mun.pk, 'parte_naran': 'Maria',
			'meius': 'SOSA', 'sosa_husi_se': 'Joao', 'sosa_sasin': 'SIN', 'sasin_1': 'Sasin A',
			'eransa_husi_se': 'la relevante', 'sosa_akordu': 'LAE', 'sosa_akordu_fatin': 'subar',
			'dok_identifikasaun': ['BI'], 'fotografia': ['UMA', 'NATAR']}
		d.update(extra)
		return d


class SurveiWebTest(SurveiBase):
	def test_labele_input_la_iha_autorizasaun(self):
		self.client.force_login(self.legal)
		r = self.client.get(reverse('legal-survei-add'))
		self.assertRedirects(r, reverse('legal-survei-list'))
		self.assertNotContains(self.client.get(reverse('home')), reverse('legal-survei-add'))

	def test_autorizasaun_futuru_seidauk_ativu(self):
		give_offline(self.legal, by=self.admin, hahu=timezone.localdate() + timedelta(days=2))
		self.client.force_login(self.legal)
		self.assertEqual(self.client.get(reverse('legal-survei-add')).status_code, 302)

	def test_input_haruka_hamoos_grupu_subar(self):
		give_offline(self.legal, by=self.admin)
		self.client.force_login(self.legal)
		self.assertContains(self.client.get(reverse('home')), reverse('legal-survei-add'))
		with self.captureOnCommitCallbacks(execute=True):
			r = self.client.post(reverse('legal-survei-add'), dict(self.dadus(), aksaun='haruka'))
		s = SurveiLegal.objects.get()
		self.assertRedirects(r, reverse('legal-survei-detail', args=[s.pk]))
		self.assertEqual(s.status, SurveiLegal.HARUKA)
		self.assertTrue(s.kode.startswith('LGL-LIQ-'))
		self.assertEqual(s.eransa_husi_se, '')              # meius la'ós eransa
		self.assertEqual(s.sosa_akordu_fatin, '')           # akordu = LAE
		self.assertEqual(s.sasin_1, 'Sasin A')
		self.assertEqual(s.fotografia, ['UMA', 'NATAR'])
		self.assertTrue(Notification.objects.filter(recipient=self.admin).exists())

	def test_kazu_sibar_kopia_fatin(self):
		give_offline(self.legal, by=self.admin)
		self.client.force_login(self.legal)
		self.client.post(reverse('legal-survei-add'), self.dadus(kazu=self.kazu.pk, munisipiu=''))
		s = SurveiLegal.objects.get()
		self.assertEqual(s.munisipiu, self.kazu.munisipiu)
		self.assertEqual(s.status, SurveiLegal.RASCUNHO)

	def test_kazu_foun_presiza_munisipiu(self):
		give_offline(self.legal, by=self.admin)
		self.client.force_login(self.legal)
		r = self.client.post(reverse('legal-survei-add'), self.dadus(munisipiu=''))
		self.assertEqual(r.status_code, 200)
		self.assertFalse(SurveiLegal.objects.exists())

	def test_admin_verifika_rejeita_no_asesu(self):
		give_offline(self.legal, by=self.admin)
		self.client.force_login(self.legal)
		self.client.post(reverse('legal-survei-add'), dict(self.dadus(), aksaun='haruka'))
		s = SurveiLegal.objects.get()
		self.client.force_login(self.analista)
		self.assertEqual(self.client.get(reverse('legal-survei-detail', args=[s.pk])).status_code, 403)
		self.client.force_login(self.admin)
		self.client.post(reverse('legal-survei-verifika', args=[s.pk]), {'aksaun': 'rejeita', 'nota': ''})
		s.refresh_from_db()
		self.assertEqual(s.status, SurveiLegal.HARUKA)       # razaun obrigatóriu
		self.client.post(reverse('legal-survei-verifika', args=[s.pk]), {'aksaun': 'rejeita', 'nota': 'Falta dokumentu'})
		s.refresh_from_db()
		self.assertEqual(s.status, SurveiLegal.REJEITADU)
		self.client.force_login(self.legal)
		self.assertEqual(self.client.get(reverse('legal-survei-update', args=[s.pk])).status_code, 200)

	def test_upload_no_download_file(self):
		give_offline(self.legal, by=self.admin)
		self.client.force_login(self.legal)
		self.client.post(reverse('legal-survei-add'), self.dadus())
		s = SurveiLegal.objects.get()
		self.client.post(reverse('legal-survei-file-add', args=[s.pk]), {'tipu': 'FOTO', 'naran': 'uma', 'file': SimpleUploadedFile('a.jpg', JPG)})
		self.client.post(reverse('legal-survei-file-add', args=[s.pk]), {'tipu': 'FOTO', 'file': SimpleUploadedFile('a.jpg', b'falsu')})
		self.assertEqual(s.files.count(), 1)
		f = s.files.get()
		self.client.force_login(self.admin)
		self.assertEqual(self.client.get(reverse('legal-survei-file', args=[f.pk])).status_code, 404)   # rascunho: Admin la haree
		self.client.force_login(self.inv)
		self.assertEqual(self.client.get(reverse('legal-survei-file', args=[f.pk])).status_code, 403)

	def test_dashboard(self):
		for u in (self.legal, self.admin, self.analista):
			self.client.force_login(u)
			self.assertEqual(self.client.get(reverse('legal-dash')).status_code, 200)
		self.client.force_login(self.inv)
		self.assertEqual(self.client.get(reverse('legal-dash')).status_code, 403)


class SurveiAPITest(SurveiBase):
	def api(self, user):
		from django.test import Client
		return Client(HTTP_AUTHORIZATION='Bearer ' + str(RefreshToken.for_user(user).access_token))

	def test_sinkron_survei_husi_hp(self):
		give_offline(self.legal, by=self.admin)
		c = self.api(self.legal)
		r = c.get(reverse('api-sinkron-legal-opsaun'))
		self.assertEqual(r.status_code, 200)
		self.assertIn(str(self.kazu.pk), [k['id'] for k in r.json()['kazu']])
		sid = str(_uuid.uuid4())
		body = dict(self.dadus(), id=sid, kria_iha=timezone.now().isoformat())
		url = reverse('api-sinkron-survei')
		self.assertEqual(c.post(url, _json.dumps(body), content_type='application/json').status_code, 201)
		self.assertEqual(c.post(url, _json.dumps(body), content_type='application/json').status_code, 200)   # idempotente
		fid = str(_uuid.uuid4())
		furl = reverse('api-sinkron-survei-file', args=[sid])
		self.assertEqual(c.post(furl, {'id': fid, 'tipu': 'DOKUMENTU', 'file': SimpleUploadedFile('d.jpg', JPG)}).status_code, 201)
		self.assertEqual(c.post(furl, {'id': fid, 'tipu': 'DOKUMENTU', 'file': SimpleUploadedFile('d.jpg', JPG)}).status_code, 200)
		r = c.post(reverse('api-sinkron-survei-haruka', args=[sid]))
		self.assertEqual(r.json()['status'], SurveiLegal.HARUKA)
		s = SurveiLegal.objects.get(pk=sid)
		self.assertEqual((s.files.count(), s.eransa_husi_se, s.created_by), (1, '', self.legal))

	def test_sinkron_liur_periodu_autorizasaun(self):
		perm = give_offline(self.legal, by=self.admin)
		OfflinePermission.objects.filter(pk=perm.pk).update(start_date=timezone.now() - timedelta(days=9), end_date=timezone.now() - timedelta(days=2))
		body = dict(self.dadus(), id=str(_uuid.uuid4()), kria_iha=timezone.now().isoformat())
		r = self.api(self.legal).post(reverse('api-sinkron-survei'), _json.dumps(body), content_type='application/json')
		self.assertEqual(r.status_code, 400)

	def test_investigador_labele_uza_api_legal(self):
		give_offline(self.inv, by=self.admin)
		self.assertEqual(self.api(self.inv).get(reverse('api-sinkron-survei')).status_code, 403)
		self.assertEqual(self.api(self.legal).get(reverse('api-sinkron-opsaun')).status_code, 403)


class AutorizasaunLegalTest(SurveiBase):
	def test_admin_no_superadmin_ativa_input(self):
		sa = make_user(SUPERADMIN)
		for u in (self.admin, sa):
			self.client.force_login(u)
			self.assertContains(self.client.get(reverse('legal-kazu-list')), reverse('legal-autorizasaun'))
			r = self.client.post(reverse('legal-autorizasaun'), {'users': [self.legal.pk], 'data_remata': str(timezone.localdate() + timedelta(days=3))})
			self.assertRedirects(r, reverse('legal-autorizasaun'))
		self.client.force_login(self.legal)
		self.assertEqual(self.client.get(reverse('legal-survei-add')).status_code, 200)
		self.assertEqual(OfflinePermission.objects.filter(user=self.legal, is_active=True).count(), 1)
		perm = OfflinePermission.objects.get(user=self.legal, is_active=True)
		self.client.force_login(self.admin)
		self.client.post(reverse('legal-autorizasaun-kansela', args=[perm.pk]))
		self.client.force_login(self.legal)
		self.assertEqual(self.client.get(reverse('legal-survei-add')).status_code, 302)

	def test_la_bele_hili_investigador_no_asesu(self):
		self.client.force_login(self.admin)
		r = self.client.post(reverse('legal-autorizasaun'), {'users': [self.inv.pk]})
		self.assertEqual(r.status_code, 200)
		self.assertFalse(OfflinePermission.objects.filter(user=self.inv).exists())
		for u in (self.legal, self.analista):
			self.client.force_login(u)
			self.assertEqual(self.client.get(reverse('legal-autorizasaun')).status_code, 403)
