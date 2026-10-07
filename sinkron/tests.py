import io
import shutil
import tempfile
import uuid
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from config.rbac import ADMIN, SUPERADMIN, INVESTIGADOR
from config.testing import setup_master, make_user, PASSWORD
from custom.models import Munisipiu, PostuAdministrativu, Suku, TipuKonflitu, NesesidadeUrjente, TipuAtor, TipuEviksaun
from kazu.models import Kazu, Evidensia, KazuHistoria
from notification.models import Notification
from users.models import OfflinePermission
from users.services import cancel_offline

MEDIA = tempfile.mkdtemp()


def jpg(nome='foto.jpg'):
	buf = io.BytesIO()
	Image.new('RGB', (2400, 1600), (90, 140, 70)).save(buf, 'JPEG')
	return SimpleUploadedFile(nome, buf.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=MEDIA)
class SinkronBase(TestCase):
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
		self.perm = OfflinePermission.objects.create(user=self.inv, given_by=self.admin)
		self.token = self.login()

	def login(self, email='maria@teste.tl'):
		r = self.client.post(reverse('api-token'), {'username': email, 'password': PASSWORD})
		return r.json().get('access')

	def auth(self):
		return {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

	def payload(self, **extra):
		hoje = timezone.localdate().isoformat()
		data = {
			'id': str(uuid.uuid4()), 'kria_iha': timezone.now().isoformat(),
			'titulu': 'Eviksaun Maubara', 'data_relatoriu': hoje, 'postu': self.postu.pk, 'suku': self.suku.pk, 'aldeia': '',
			'latitude': -8.6121234567, 'longitude': 125.2107654321, 'gps_akurasia': 9,
			'data_akontesimentu': hoje, 'tipu_konflitu': [TipuKonflitu.objects.get(code='DESLOKAMENTU').pk],
			'deskrisaun': 'Familia 15 hetan avizu atu sai.', 'konsentimentu': True,
			'nesesidade': [NesesidadeUrjente.objects.get(code='APOIU-LEGAL').pk],
			'afetadu': [{'uma_kain': 15, 'total_ema': 72, 'mane': 34, 'feto': 38}],
			'insidente': [{'tipu_eviksaun': TipuEviksaun.objects.first().pk, 'loron_avizu': 3, 'forsa_seguransa': True}],
			'ator': [{'tipu_ator': TipuAtor.objects.get(code='POLISIA').pk, 'naran': 'PNTL'}],
		}
		data.update(extra)
		return data

	def send(self, data):
		return self.client.post(reverse('api-sinkron-kazu'), data, content_type='application/json', **self.auth())

	def upload(self, kazu_id, tipu='FOTO', f=None, ev_id=None):
		return self.client.post(reverse('api-sinkron-evidensia', args=[kazu_id]),
			{'id': ev_id or str(uuid.uuid4()), 'tipu': tipu, 'file': f or jpg()}, **self.auth())

	def haruka(self, kazu_id):
		with self.captureOnCommitCallbacks(execute=True):
			return self.client.post(reverse('api-sinkron-haruka', args=[kazu_id]), **self.auth())


class FluxuSinkronTest(SinkronBase):
	def test_fluxu_kompletu(self):
		data = self.payload()
		r = self.send(data)
		self.assertEqual(r.status_code, 201, r.content)
		kazu = Kazu.objects.get(pk=data['id'])
		self.assertEqual(kazu.status, 'PENDING')
		self.assertEqual(kazu.munisipiu, self.liq)
		self.assertEqual(str(kazu.latitude), '-8.612123')           # arredonda ba desimál 6
		self.assertTrue(kazu.urjente)
		self.assertEqual(kazu.afetadu.get().total_ema, 72)
		self.assertEqual(kazu.insidente.count(), 1)
		self.assertTrue(KazuHistoria.objects.filter(kazu=kazu, nota='SINKRON').exists())

		self.assertEqual(self.upload(kazu.pk).status_code, 201)
		ev = Evidensia.objects.get(kazu=kazu)
		self.assertTrue(ev.file.name.endswith('.jpg'))

		r = self.haruka(kazu.pk)
		self.assertEqual(r.status_code, 200)
		kazu.refresh_from_db()
		self.assertEqual(kazu.status, 'SYNCED')
		self.assertTrue(kazu.kode.startswith('SMKRE-LIQ-'))
		self.assertEqual(r.json()['kode'], kazu.kode)
		self.assertTrue(Notification.objects.filter(recipient=self.admin).exists())

	def test_idempotente_koko_fali(self):
		data = self.payload()
		self.assertEqual(self.send(data).status_code, 201)
		self.assertEqual(self.send(data).status_code, 200)            # koneksaun kotu → haruka fali
		self.assertEqual(Kazu.objects.filter(pk=data['id']).count(), 1)
		self.assertEqual(Kazu.objects.get(pk=data['id']).afetadu.count(), 1)
		ev_id = str(uuid.uuid4())
		self.assertEqual(self.upload(data['id'], ev_id=ev_id).status_code, 201)
		self.assertEqual(self.upload(data['id'], ev_id=ev_id).status_code, 200)
		self.assertEqual(Evidensia.objects.filter(kazu_id=data['id']).count(), 1)
		self.haruka(data['id'])
		kode = Kazu.objects.get(pk=data['id']).kode
		r = self.haruka(data['id'])                                   # haruka dala rua → kódigu hanesan
		self.assertEqual(r.json()['kode'], kode)
		r = self.send(data)                                           # dadus haruka ona → la muda
		self.assertEqual(r.status_code, 200)
		self.assertEqual(r.json()['status'], 'SYNCED')

	def test_validasaun_hanesan_web(self):
		r = self.send(self.payload(latitude=-6.2, longitude=106.8))    # Jakarta → li'ur TL
		self.assertEqual(r.status_code, 400)
		self.assertIn('latitude', r.json()['erru'])
		r = self.send(self.payload(gps_akurasia=120))
		self.assertIn('gps_akurasia', r.json()['erru'])
		r = self.send(self.payload(konsentimentu=False))
		self.assertIn('konsentimentu', r.json()['erru'])
		r = self.send(self.payload(afetadu=[{'total_ema': 10, 'mane': 3, 'feto': 3}]))
		self.assertIn('afetadu.0.total_ema', r.json()['erru'])
		self.assertEqual(Kazu.objects.count(), 0)

	def test_munisipiu_husi_knaar_la_husi_hp(self):
		dil_postu = PostuAdministrativu.objects.filter(munisipiu__code='DIL').first()
		r = self.send(self.payload(postu=dil_postu.pk, munisipiu=Munisipiu.objects.get(code='DIL').pk))
		self.assertEqual(r.status_code, 400)                          # postu Dili la iha Liquiçá
		self.assertIn('postu', r.json()['erru'])

	def test_foto_maximu_5_no_tipu(self):
		data = self.payload()
		self.send(data)
		for _i in range(5):
			self.assertEqual(self.upload(data['id']).status_code, 201)
		self.assertEqual(self.upload(data['id']).status_code, 400)
		r = self.upload(data['id'], tipu='DOKUMENTU')
		self.assertEqual(r.status_code, 400)


class LaPublikaTest(SinkronBase):
	def test_la_publika_husi_hp(self):
		# Komunidade husu atu kazu la mosu iha portal: marka iha HP → tama iha servidór
		data = self.payload(la_publika=True)
		self.assertEqual(self.send(data).status_code, 201)
		self.assertTrue(Kazu.objects.get(pk=data['id']).la_publika)
		data = self.payload()
		self.send(data)
		self.assertFalse(Kazu.objects.get(pk=data['id']).la_publika)


class EvidensiaSinkronTest(SinkronBase):
	def test_video_husi_hp_iha_file(self):
		# Regresaun: vídeo husi HP tenke rai ho file (la'ós evidénsia mamuk)
		from django.core.files.uploadedfile import SimpleUploadedFile
		data = self.payload()
		self.send(data)
		r = self.upload(data['id'], tipu='VIDEO', f=SimpleUploadedFile('v.mp4', b'\x00\x00\x00\x18ftypmp42' + b'0' * 64, 'video/mp4'))
		self.assertEqual(r.status_code, 201, r.content)
		ev = Evidensia.objects.get(kazu_id=data['id'], tipu='VIDEO')
		self.assertTrue(ev.file.name.endswith('.mp4'))
		r = self.upload(data['id'])
		self.assertTrue(Evidensia.objects.get(kazu_id=data['id'], tipu='FOTO').file)


class AutorizasaunSinkronTest(SinkronBase):
	def test_kazu_kria_li_ur_periodu_rejeita(self):
		r = self.send(self.payload(kria_iha=(timezone.now() - timedelta(days=3)).isoformat()))
		self.assertEqual(r.status_code, 400)                          # antes autorizasaun hahú
		r = self.send(self.payload(kria_iha=(timezone.now() + timedelta(days=1)).isoformat()))
		self.assertEqual(r.status_code, 400)                          # futuru

	def test_autorizasaun_remata_bele_sinkron_kazu_uluk(self):
		# Kazu kria oras 2 liu ba; autorizasaun remata oras 1 liu ba → sinkron nafatin
		agora = timezone.now()
		OfflinePermission.objects.filter(pk=self.perm.pk).update(start_date=agora - timedelta(days=5), end_date=agora - timedelta(hours=1))
		self.token = self.login()
		self.assertEqual(self.send(self.payload(kria_iha=(agora - timedelta(hours=2)).isoformat())).status_code, 201)
		# Kazu kria depois remata → rejeita
		self.assertEqual(self.send(self.payload(kria_iha=agora.isoformat())).status_code, 400)

	def test_kansela_la_simu_kazu_foun(self):
		cancel_offline(self.inv, by=self.admin)
		self.token = self.login()                                     # token foun (sinkron deit)
		r = self.send(self.payload(kria_iha=(timezone.now() + timedelta(minutes=1)).isoformat()))
		self.assertEqual(r.status_code, 400)

	def test_papel_seluk_ka_la_iha_token(self):
		self.assertEqual(self.client.get(reverse('api-sinkron-opsaun')).status_code, 401)
		self.client.force_login(self.admin)                           # sesaun web la sufisiente (JWT deit)
		self.assertEqual(self.client.get(reverse('api-sinkron-opsaun')).status_code, 401)

	def test_investigador_seluk_labele_toka(self):
		data = self.payload()
		self.send(data)
		outro = make_user(INVESTIGADOR, email='joao@teste.tl', munisipiu_code='LIQ')
		OfflinePermission.objects.create(user=outro, given_by=self.admin)
		self.token = self.login('joao@teste.tl')
		self.assertEqual(self.send(data).status_code, 403)
		self.assertEqual(self.upload(data['id']).status_code, 404)
		self.assertEqual(self.haruka(data['id']).status_code, 404)


class OpsaunTest(SinkronBase):
	def test_opsaun_munisipiu_knaar_deit(self):
		r = self.client.get(reverse('api-sinkron-opsaun'), **self.auth())
		self.assertEqual(r.status_code, 200)
		d = r.json()
		self.assertEqual(d['munisipiu']['code'], 'LIQ')
		self.assertTrue(all(p['id'] in PostuAdministrativu.objects.filter(munisipiu=self.liq).values_list('id', flat=True) for p in d['postu']))
		self.assertEqual(d['suku'][0]['postu_id'], self.postu.pk)
		self.assertTrue(any(t['presiza_esplika'] for t in d['tipu_konflitu']))

	def test_lista_status_server(self):
		data = self.payload()
		self.send(data)
		r = self.client.get(reverse('api-sinkron-kazu'), **self.auth())
		self.assertEqual(r.json()['kazu'][0]['status'], 'PENDING')


class AppPageTest(TestCase):
	def test_pajina_app_la_iha_dadus_privadu(self):
		r = self.client.get(reverse('sinkron'))
		self.assertEqual(r.status_code, 200)                          # SW bele rai iha cache (la presiza login)
		self.assertContains(r, 'smkre_offline.js')
		self.assertNotIn(b'csrfmiddlewaretoken', r.content)


class KomanduTesteTest(SinkronBase):
	def test_cek_sinkron_hatudu_kazu_husi_hp(self):
		from io import StringIO
		from django.core.management import call_command
		data = self.payload()
		self.send(data)
		self.upload(data['id'])
		self.haruka(data['id'])
		out = StringIO()
		call_command('cek_sinkron', stdout=out)
		self.assertIn(Kazu.objects.get(pk=data['id']).kode, out.getvalue())
		self.assertIn('1 kompletu', out.getvalue())

	@override_settings(DEBUG=False)
	def test_teste_offline_labele_iha_production(self):
		from django.core.management import call_command
		from django.core.management.base import CommandError
		with self.assertRaises(CommandError):
			call_command('teste_offline')

	@override_settings(DEBUG=True)
	def test_teste_offline_prepara_konta(self):
		from io import StringIO
		from django.core.management import call_command
		call_command('teste_offline', '--email', 'hp@teste.tl', '--munisipiu', 'DIL', stdout=StringIO())
		self.assertEqual(self.client.post(reverse('api-token'), {'username': 'hp@teste.tl', 'password': 'Teste#Offline-2026'}).json()['offline_ativu'], True)
