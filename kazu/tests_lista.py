"""Lista: pájina 10, foun liu iha leten (númeru 1), númeru kontinua, filtru la lakon; notifikasaun 🔔 máximu 5."""
from datetime import timedelta
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from config.rbac import ADMIN, INVESTIGADOR
from config.testing import setup_master, make_user
from custom.models import Munisipiu
from kazu.models import Kazu, VERIFIED
from notification.models import Notification


class ListaPajinaTest(TestCase):
	def setUp(self):
		setup_master()
		self.liq = Munisipiu.objects.get(code='LIQ')
		self.admin = make_user(ADMIN)
		self.inv = make_user(INVESTIGADOR, email='inv@teste.tl')
		agora = timezone.now()
		for i in range(23):                         # kazu 0 = tuan liu · kazu 22 = foun liu
			k = Kazu.objects.create(munisipiu=self.liq, created_by=self.inv, titulu=f'Kazu {i:02d}', status=VERIFIED)
			Kazu.objects.filter(pk=k.pk).update(created_at=agora - timedelta(hours=100 - i))
		self.client.force_login(self.admin)

	def test_pajina_10_foun_liu_iha_leten(self):
		r = self.client.get(reverse('kazu-list'))
		pajina = r.context['objects']
		self.assertEqual(len(pajina), 10)
		self.assertEqual(pajina[0].titulu, 'Kazu 22')                 # númeru 1 = foun liu
		self.assertEqual(pajina.paginator.count, 23)
		self.assertContains(r, 'Hatudu 1–10 husi 23')
		r = self.client.get(reverse('kazu-list'), {'page': 2})
		self.assertEqual(r.context['objects'][0].titulu, 'Kazu 12')
		self.assertContains(r, 'data-label="#">11</td>')                 # númeru kontinua
		r = self.client.get(reverse('kazu-list'), {'page': 3})
		self.assertEqual(len(r.context['objects']), 3)
		self.assertEqual(r.context['objects'][2].titulu, 'Kazu 00')    # ikus = tuan liu
		self.assertContains(r, 'data-label="#">23</td>')

	def test_pajina_sala_la_halo_erru(self):
		for p in ('abc', '999', '-1', ''):
			r = self.client.get(reverse('kazu-list'), {'page': p})
			self.assertEqual(r.status_code, 200, p)

	def test_filtru_la_lakon_iha_link_pajina(self):
		r = self.client.get(reverse('kazu-list'), {'status': VERIFIED, 'q': 'Kazu'})
		self.assertContains(r, 'status=VERIFIED')
		self.assertContains(r, 'q=Kazu')
		self.assertContains(r, 'page=2')

	def test_query_konstante(self):
		# Kódigu kmaan: númeru query la sa'e tuir kazu barak (la iha N+1)
		with CaptureQueriesContext(connection) as c10:
			self.client.get(reverse('kazu-list'))
		Kazu.objects.create(munisipiu=self.liq, created_by=self.inv, titulu='Foun', status=VERIFIED)
		with CaptureQueriesContext(connection) as c11:
			self.client.get(reverse('kazu-list'))
		self.assertEqual(len(c10), len(c11))

	def test_relatoriu_lista_pajina(self):
		r = self.client.get(reverse('report-list'))
		self.assertEqual(r.status_code, 200)
		self.assertEqual(len(r.context['objects']), 10)
		self.assertNotContains(r, 'pdfmake')                          # JS todan la iha ona

	def test_lista_seluk_pajina(self):
		for nome in ('pesoal-list', 'offline-list', 'notification-list'):
			r = self.client.get(reverse(nome))
			self.assertEqual(r.status_code, 200, nome)
			self.assertTrue(hasattr(r.context['objects'], 'paginator'), nome)


class NotifMaximuTest(TestCase):
	def setUp(self):
		setup_master()
		self.admin = make_user(ADMIN)
		for i in range(12):
			Notification.objects.create(recipient=self.admin, message=f'Notif {i}', is_urgent=(i == 0))
		self.client.force_login(self.admin)

	def test_dropdown_maximu_5_urjente_uluk(self):
		r = self.client.get('/api/notif/Notifikasaun/ikus/')
		d = r.json()
		self.assertEqual(len(d['objects']), 5)
		self.assertTrue(d['objects'][0]['urgent'])
		self.assertEqual(self.client.get('/api/notif/Notifikasaun/total/').json()['value'], 12)   # badge: total loos

	def test_lista_notif_pajina_10(self):
		r = self.client.get(reverse('notification-list'))
		self.assertEqual(len(r.context['objects']), 10)
		self.assertEqual(r.context['objects'][0].message, 'Notif 11')       # foun liu iha leten


class MapaGpsTest(TestCase):
	def test_kazu_la_iha_longitude_la_tama_mapa(self):
		setup_master()
		admin = make_user(ADMIN)
		inv = make_user(INVESTIGADOR, email='i2@teste.tl')
		liq = Munisipiu.objects.get(code='LIQ')
		Kazu.objects.create(munisipiu=liq, created_by=inv, status=VERIFIED, latitude='-8.6')        # longitude mamuk
		Kazu.objects.create(munisipiu=liq, created_by=inv, status=VERIFIED, latitude='-8.6', longitude='125.2')
		self.client.force_login(admin)
		r = self.client.get(reverse('report-mapa'))
		self.assertEqual(r.status_code, 200)
		self.assertNotContains(r, 'None')                               # la iha koordenada mamuk iha JS
