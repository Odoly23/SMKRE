from django.test import TestCase
from django.urls import reverse
from config.rbac import ADMIN, INVESTIGADOR, ANALISTA, OFISIAL_LEGAL, SUPERADMIN
from config.testing import setup_master, make_user


class HomeTest(TestCase):
	def setUp(self):
		setup_master()

	def test_home_presiza_login(self):
		self.assertRedirects(self.client.get('/'), reverse('login') + '?next=/')

	def test_home_tuir_papel(self):
		self.client.force_login(make_user(INVESTIGADOR))
		r = self.client.get('/')
		self.assertTemplateUsed(r, 'home/home_investigador.html')
		self.assertContains(r, 'class="bnav"')           # menu okos ba Investigadór
		for role in (SUPERADMIN, ADMIN, ANALISTA, OFISIAL_LEGAL):
			self.client.force_login(make_user(role))
			r = self.client.get('/')
			self.assertTemplateUsed(r, 'home/home.html')
			self.assertNotContains(r, 'class="bnav"')

	def test_menu_tuir_rbac(self):
		self.client.force_login(make_user(ANALISTA))
		self.assertNotContains(self.client.get('/'), reverse('pesoal-list'))
		self.client.force_login(make_user(ADMIN))
		self.assertContains(self.client.get('/'), reverse('pesoal-list'))


class SeguransaTest(TestCase):
	def test_header_seguransa(self):
		r = self.client.get(reverse('login'))
		self.assertIn("script-src 'self'", r['Content-Security-Policy'])
		self.assertIn('geolocation=(self)', r['Permissions-Policy'])
		self.assertEqual(r['X-Frame-Options'], 'SAMEORIGIN')
		self.assertIn('no-store', r['Cache-Control'])
		self.assertContains(r, 'name="author" content="Onosio, Ricardo, Olavio"')
		self.assertContains(r, 'noindex, nofollow')

	def test_logout_tenke_post(self):
		setup_master()
		self.client.force_login(make_user(ADMIN))
		self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
		self.assertEqual(self.client.post(reverse('logout')).status_code, 302)

	def test_pwa(self):
		m = self.client.get(reverse('manifest')).json()
		self.assertEqual(m['short_name'], 'SMKRE')
		r = self.client.get(reverse('service-worker'))
		self.assertEqual(r['Service-Worker-Allowed'], '/')
		self.assertNotIn('no-store', r['Cache-Control'])

	def test_404_tetun(self):
		r = self.client.get('/la-iha/')
		self.assertEqual(r.status_code, 404)


class MediaTest(TestCase):
	def test_media_presiza_login_no_path_seguru(self):
		self.assertEqual(self.client.get('/media/pesoal/1/foto.png').status_code, 302)
		setup_master()
		self.client.force_login(make_user(ADMIN))
		self.assertEqual(self.client.get('/media/pesoal/../../smkre/settings.py').status_code, 404)
		self.assertEqual(self.client.get('/media/seluk/x.png').status_code, 404)
