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
		self.tipu = TipuKonflitu.objects.get(code='GOV-RAI-ESTADU')
		self.n = 0
		# Dili: 4 aprovadu · Liquiçá: 2 aprovadu (tenke subar "< 3")
		for _i in range(4):
			self.kazu(self.dil)
		for _i in range(2):
			self.kazu(self.liq)
		# Dili mós: verifikadu + la iha konsentimentu (KONTA iha portal) · la publika (LA konta)
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
	def test_kazu_hotu_exetu_la_publika(self):
		d = estatistika({})
		self.assertEqual(d['kpi']['total'], {'n': 8, 'label': '8'})
		self.assertEqual(d['kpi']['ema'], 160)

	def test_numeru_ki_ik_subar(self):
		d = estatistika({})
		mun = {m['code']: m for m in d['munisipiu']}
		self.assertEqual(mun['DIL']['n'], 6)
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


class MapaPinTest(PortalBase):
	def test_kartaun_munisipiu_boot_deit(self):
		mun = {m['code']: m for m in estatistika({})['munisipiu']}
		self.assertEqual(mun['DIL']['uma_kain'], 30)                   # 6 kazu × 5
		self.assertEqual(mun['DIL']['tipu_top'], self.tipu.name)
		self.assertNotIn('uma_kain', mun['LIQ'])                       # "< 3": la iha detalla
		self.assertNotIn('tipu_top', mun['LIQ'])

	def test_lokasaun_aproksimadu_bainhira_hili_munisipiu(self):
		Kazu.objects.filter(munisipiu=self.dil).update(latitude='-8.556789', longitude='125.578912')
		Kazu.objects.filter(munisipiu=self.liq).update(latitude='-8.612345', longitude='125.212345')
		self.assertEqual(estatistika({})['lokasaun'], [])               # la hili munisípiu: la iha pontu
		self.assertEqual(estatistika({'munisipiu': 'DIL'})['lokasaun'], [(-8.56, 125.58)])   # ~1 km, hamutuk ida
		self.assertEqual(estatistika({'munisipiu': 'LIQ'})['lokasaun'], [])                  # "< 3": la hatudu
		r = self.client.get(reverse('api-portal-estatistika'), {'munisipiu': 'DIL'})
		self.assertNotIn(b'578912', r.content)                         # koordenada loos la sai


class PortalPajinaTest(PortalBase):
	@override_settings(PORTAL_TELEFONE='+670 7000 0000', PORTAL_EMAIL='info@exemplu.tl')
	def test_portal_publiku_ho_kontaktu(self):
		r = self.client.get(reverse('portal'))
		self.assertEqual(r.status_code, 200)
		self.assertContains(r, 'tel:+67070000000')
		self.assertContains(r, 'mailto:info@exemplu.tl')
		self.assertContains(r, 'main/portal/landing.js')
		self.assertContains(r, 'data-api="/api/portal/estatistika/"')     # dadus hotu husi API
		self.assertNotContains(r, 'Tama-Lai')                              # la iha link login
		self.assertNotContains(r, '/login')

	def test_publikasaun_rascunho_subar(self):
		pub = Publikasaun.objects.create(titulu='Draft', rezumu='x', data=timezone.localdate(),
			file=SimpleUploadedFile('a.pdf', PDF))
		self.assertEqual(self.client.get(reverse('portal-publikasaun', args=[pub.pk])).status_code, 404)
		self.assertNotContains(self.client.get(reverse('portal')), 'Draft')
		pub.status = Publikasaun.PUBLIKADU
		pub.save()
		self.assertEqual(self.client.get(reverse('portal-publikasaun', args=[pub.pk])).status_code, 200)
		self.assertNotContains(self.client.get(reverse('portal')), 'Draft')     # policy brief la mosu tan iha landing


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


class EviksaunPubliku(PortalBase):
	# marka kazu Dili sira hetan eviksaun (seksaun eviksaun liu husi property Kazu)
	def marka(self, mun, n, konsulta='LAE'):
		for k in Kazu.objects.filter(munisipiu=mun, status='APPROVED', konsentimentu=True, la_publika=False)[:n]:
			k.eviksaun_akontese, k.konsultasaun_molok = 'SIN', konsulta
			k.save()

	def test_painel_eviksaun_agregadu(self):
		self.marka(self.dil, 3)
		ev = estatistika({})['eviksaun']
		self.assertEqual(ev['total'], {'n': 3, 'label': '3'})
		self.assertEqual(ev['uma_kain'], 15)
		self.assertEqual([(x['code'], x['n']) for x in ev['konsultasaun']], [('LAE', 3), ('SIN', 0), ('LAHATENE', 0), ('LAIHA', 0)])
		self.assertEqual(estatistika({})['kpi']['eviksaun'], ev['total'])

	def test_eviksaun_ki_ik_la_hatudu_detalla(self):
		self.marka(self.liq, 2)
		ev = estatistika({})['eviksaun']
		self.assertEqual(ev['total'], {'n': None, 'label': '< 3'})
		self.assertIsNone(ev['uma_kain'])
		self.assertEqual({x['label'] for x in ev['konsultasaun']}, {'–'})          # 1–2 kazu: la hatudu númeru
		self.assertEqual(len(ev['konsultasaun']), 4)                                # gráfiku sempre iha kategoria

	def test_api_publiku_la_iha_dadus_internu(self):
		r = self.client.get(reverse('api-portal-estatistika'))
		self.assertEqual(r.status_code, 200)
		for internu in (b'urjente', b'hein', b'verifikasaun', b'kode', b'latitude', b'survei'):
			self.assertNotIn(internu, r.content.lower())


class MapaPontuLandingTest(PortalBase):
	# mapa landing: fatin aproksimadu (~1 km), munisípiu ho kazu ≥ 3 de'it, la iha koordenada loos
	def test_pontu_aproksimadu_no_privasidade(self):
		Kazu.objects.filter(munisipiu=self.dil).update(latitude='-8.556789', longitude='125.578912')   # 6 kazu GPS hanesan (la publika la konta)
		Kazu.objects.filter(munisipiu=self.liq).update(latitude='-8.612345', longitude='125.212345')   # 2 kazu → la hatudu
		pontu = estatistika({})['pontu']
		self.assertEqual(pontu, [{'lat': -8.56, 'lng': 125.58, 'mun': self.dil.name, 'n': 6, 'label': '6'}])   # kazu 6 konta hotu
		r = self.client.get(reverse('api-portal-estatistika'))
		self.assertNotIn(b'578912', r.content)
		self.assertNotIn(b'212345', r.content)


class TipuTuanTest(PortalBase):
	# kazu ho tipu tuan (la ativu ona) tenke mosu iha gráfiku tipu (la'ós 0 hotu)
	def test_tipu_la_ativu_ne_ebe_uza_mosu(self):
		TipuKonflitu.objects.filter(pk=self.tipu.pk).update(is_active=False)
		tipu = {t['id']: t for t in estatistika({})['tipu']}
		self.assertEqual(tipu[self.tipu.pk]['n'], 8)
		self.assertNotIn(TipuKonflitu.objects.filter(is_active=False).exclude(pk=self.tipu.pk).values_list('pk', flat=True).first(), tipu)


class FulanTest(PortalBase):
	# kazu kada fulan (fulan 12 ikus) ho privasidade "< 3"
	def test_fulan_12_ho_subar(self):
		fulan = estatistika({})['fulan']
		self.assertEqual(len(fulan), 12)
		self.assertEqual(fulan[-1]['n'], 8)                       # kazu 8 iha fulan ida ne'e
		self.assertTrue(all(f['n'] == 0 for f in fulan[:-1]))
		Kazu.objects.filter(munisipiu=self.dil).update(status='DRAFT')       # rascunho la konta: restu 2 → "< 3"
		cache.clear()                                             # API públiku iha cache minutu 10
		self.assertEqual(estatistika({})['fulan'][-1]['label'], '< 3')


class BazeIdaTest(PortalBase):
	# KPI, mapa no gráfiku uza baze IDA: kazu hotu haruka ona ba server, exetu "La publika" / rascunho / kanseladu
	def test_total_hanesan_mapa_no_grafiku(self):
		self.kazu(self.liq, status='DRAFT')
		self.kazu(self.liq, status='CANCELED')
		d = estatistika({})
		self.assertEqual(d['kpi']['total']['n'], 8)              # 6 aprovadu + verifikadu + la iha konsentimentu
		self.assertEqual(d['kpi']['munisipiu'], 2)
		self.assertEqual(sum(m['n'] or 0 for m in d['munisipiu']) + 2, 8)   # LIQ (2) subar "< 3"
		self.assertEqual(sum(t['n'] or 0 for t in d['tipu']), 8)
		self.assertEqual(sum(x['n'] or 0 for x in d['fulan']), 8)
