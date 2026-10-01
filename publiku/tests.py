import shutil
import tempfile
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from config.rbac import ADMIN, INVESTIGADOR, ANALISTA
from config.testing import setup_master, make_user
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import Kazu, UmaKainAfetada
from publiku.models import Publikasaun
from publiku.services import estatistika

MEDIA = tempfile.mkdtemp()
PDF = b'%PDF-1.4\n%%EOF\n'


@override_settings(MEDIA_ROOT=MEDIA)
class PortalBase(TestCase):
	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		shutil.rmtree(MEDIA, ignore_errors=True)

	def setUp(self):
		cache.clear()
		setup_master()
		self.inv = make_user(INVESTIGADOR)
		self.dil = Munisipiu.objects.get(code='DIL')
		self.liq = Munisipiu.objects.get(code='LIQ')
		self.tipu = TipuKonflitu.objects.get(code='DESLOKAMENTU')
		self.n = 0
		# Dili: 4 aprovadu · Liquiçá: 2 aprovadu (tenke subar "< 3")
		for _i in range(4):
			self.kazu(self.dil)
		for _i in range(2):
			self.kazu(self.liq)
		# La tama iha portal: seidauk aprova, la publika, la iha konsentimentu
		self.kazu(self.dil, status='VERIFIED')
		self.kazu(self.dil, la_publika=True)
		self.kazu(self.dil, konsentimentu=False)

	def kazu(self, mun, status='APPROVED', **extra):
		self.n += 1
		data = {'konsentimentu': True}
		data.update(extra)
		k = Kazu.objects.create(munisipiu=mun, status=status, created_by=self.inv, kode=f'P-{self.n}',
			data_relatoriu=timezone.localdate(), approved_at=timezone.now(), **data)
		k.tipu_konflitu.set([self.tipu])
		UmaKainAfetada.objects.create(kazu=k, uma_kain=5, total_ema=20, mane=9, feto=11, labarik=6)
		return k


class PrivasidadeTest(PortalBase):
	def test_kazu_aprovadu_ho_konsentimentu_deit(self):
		d = estatistika({})
		self.assertEqual(d['kpi']['total'], {'n': 6, 'label': '6'})
		self.assertEqual(d['kpi']['ema'], 120)

	def test_numeru_ki_ik_subar(self):
		d = estatistika({})
		mun = {m['code']: m for m in d['munisipiu']}
		self.assertEqual(mun['DIL']['n'], 4)
		self.assertEqual(mun['LIQ'], {'code': 'LIQ', 'name': self.liq.name, 'n': None, 'label': '< 3'})
		self.assertEqual(mun['AIL']['n'], 0)                          # zero la subar
		# Populasaun afetada: Liquiçá (2 kazu) la mosu
		self.assertEqual([a['code'] for a in d['afetadu']], ['DIL'])

	def test_filtru_ki_ik_subar_kpi_no_afetadu(self):
		d = estatistika({'munisipiu': 'liq'})
		self.assertEqual(d['filtru'], {'munisipiu': 'LIQ'})
		self.assertEqual(d['kpi']['total'], {'n': None, 'label': '< 3'})
		self.assertIsNone(d['kpi']['ema'])
		self.assertTrue(all(s['n'] is None for s in d['suku']))

	def test_api_la_haruka_numeru_loos(self):
		r = self.client.get(reverse('api-portal-estatistika'), {'munisipiu': 'LIQ'})
		self.assertEqual(r.status_code, 200)
		self.assertNotIn(b'"n":2', r.content.replace(b' ', b''))
		self.assertNotIn(b'P-', r.content)                            # la iha kódigu kazu
		self.assertNotIn(b'latitude', r.content)

	def test_filtru_la_validu_la_uza(self):
		d = estatistika({'munisipiu': "X' OR 1=1", 'tipu': 'abc', 'tinan': '1800'})
		self.assertEqual(d['filtru'], {})


class PortalPajinaTest(PortalBase):
	@override_settings(PORTAL_TELEFONE='+670 7000 0000', PORTAL_EMAIL='info@exemplu.tl')
	def test_portal_publiku_ho_kontaktu(self):
		r = self.client.get(reverse('portal'))
		self.assertEqual(r.status_code, 200)
		self.assertContains(r, 'tel:+67070000000')
		self.assertContains(r, 'mailto:info@exemplu.tl')
		self.assertContains(r, 'main/portal/portal.js')

	def test_publikasaun_rascunho_subar(self):
		pub = Publikasaun.objects.create(titulu='Draft', rezumu='x', data=timezone.localdate(),
			file=SimpleUploadedFile('a.pdf', PDF))
		self.assertEqual(self.client.get(reverse('portal-publikasaun', args=[pub.pk])).status_code, 404)
		self.assertNotContains(self.client.get(reverse('portal')), 'Draft')
		pub.status = Publikasaun.PUBLIKADU
		pub.save()
		self.assertEqual(self.client.get(reverse('portal-publikasaun', args=[pub.pk])).status_code, 200)
		self.assertContains(self.client.get(reverse('portal')), 'Draft')


@override_settings(MEDIA_ROOT=MEDIA)
class PublikasaunStafTest(TestCase):
	def setUp(self):
		setup_master()
		self.analista = make_user(ANALISTA)
		self.admin = make_user(ADMIN)
		self.inv = make_user(INVESTIGADOR)

	def data(self, conteudo=PDF):
		return {'tipu': 'POLICY', 'titulu': 'Policy brief teste', 'lian': 'tet', 'data': timezone.localdate().isoformat(),
			'rezumu': 'Rezumu', 'file': SimpleUploadedFile('brief.pdf', conteudo)}

	def test_analista_kria_admin_publika(self):
		self.client.force_login(self.analista)
		self.assertRedirects(self.client.post(reverse('publikasaun-add'), self.data()), reverse('publikasaun-list'))
		pub = Publikasaun.objects.get()
		self.assertEqual(pub.status, 'RASCUNHO')
		self.assertEqual(self.client.post(reverse('publikasaun-publika', args=[pub.pk])).status_code, 403)
		self.client.force_login(self.admin)
		self.client.post(reverse('publikasaun-publika', args=[pub.pk]))
		pub.refresh_from_db()
		self.assertEqual(pub.status, 'PUBLIKADU')
		self.assertEqual(pub.published_by, self.admin)

	def test_file_la_pdf_rejeita(self):
		self.client.force_login(self.analista)
		r = self.client.post(reverse('publikasaun-add'), self.data(b'MZ\x90 exe'))
		self.assertEqual(r.status_code, 200)
		self.assertFalse(Publikasaun.objects.exists())

	def test_investigador_labele(self):
		self.client.force_login(self.inv)
		self.assertEqual(self.client.get(reverse('publikasaun-list')).status_code, 403)


class MapboxTokenTest(TestCase):
	# Token Mapbox mai husi .env (settings.MAPBOX_TOKEN), la hakerek iha kódigu
	def test_token_husi_settings(self):
		with self.settings(MAPBOX_TOKEN='pk.teste123'):
			self.assertContains(self.client.get(reverse('portal')), 'data-mapbox="pk.teste123"')
		with self.settings(MAPBOX_TOKEN=''):
			self.assertContains(self.client.get(reverse('portal')), 'data-mapbox=""')
