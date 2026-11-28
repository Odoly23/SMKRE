"""Teste: login ida de'it kada utilizador + tab foun husu login fali."""
from datetime import timedelta
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from config.rbac import ADMIN, SUPERADMIN
from config.testing import setup_master, make_user, PASSWORD
from users.models import SesaunAtivu


@override_settings(SESAUN_IDLE_MINUTU=30)
class SesaunUnikuTest(TestCase):
	def setUp(self):
		setup_master()
		self.u = make_user(ADMIN, email='adm@teste.tl')
		self.a, self.b = Client(), Client()

	def login(self, c, **extra):
		return c.post(reverse('login'), dict({'username': 'adm@teste.tl', 'password': PASSWORD}, **extra))

	def test_dispozitivu_rua_bloka(self):
		r = self.login(self.a)
		self.assertEqual(r.status_code, 302)
		self.assertIn('_tab=', r['Location'])
		r = self.login(self.b)
		self.assertEqual(r.status_code, 200)                       # rejeita
		self.assertContains(r, 'dispozitivu seluk')

	def test_logout_depois_bele(self):
		self.login(self.a)
		self.a.post(reverse('logout'))
		self.assertFalse(SesaunAtivu.objects.filter(user=self.u).exists())
		self.assertEqual(self.login(self.b).status_code, 302)

	def test_sesaun_la_ativu_troka(self):
		self.login(self.a)
		SesaunAtivu.objects.filter(user=self.u).update(last_seen=timezone.now() - timedelta(minutes=45))
		self.assertEqual(self.login(self.b).status_code, 302)      # A la ativu → B tama
		r = self.a.get(reverse('home'))
		self.assertEqual(r.status_code, 302)                       # A sai (sesaun taka)
		self.assertNotIn('_auth_user_id', self.a.session)

	def test_admin_taka_sesaun(self):
		self.login(self.a)
		sa = make_user(SUPERADMIN, email='sa@teste.tl')
		c = Client(); c.force_login(sa)
		c.post(reverse('user-taka-sesaun', args=[self.u.pesoaluser.pesoal.uuid]))
		self.assertFalse(SesaunAtivu.objects.filter(user=self.u).exists())
		self.assertEqual(self.login(self.b).status_code, 302)

	def test_tab_foun_husu_password(self):
		self.login(self.a)
		r = self.a.get(reverse('home'))
		self.assertContains(r, 'name="sibar-tab"')                 # meta ID tab + tab_sesaun.js
		r = self.a.get(reverse('login') + '?tab=1')
		self.assertEqual(r.status_code, 200)                       # login ona, maibé tab foun hatudu formuláriu
		self.assertContains(r, 'Tab foun')
		r = self.login(self.a, tab='1')
		self.assertEqual(r.status_code, 302)                       # browser hanesan: la bloka
		self.assertIn('_tab=', r['Location'])
		self.assertEqual(len(self.a.session['tab_ids']), 2)


class TabCsrfTest(TestCase):
	# login fali iha tab foun la troka token CSRF → formuláriu iha tab tuan la falla
	def setUp(self):
		setup_master()
		self.u = make_user(ADMIN, email='adm@teste.tl')

	def test_tab_tuan_la_falla_csrf(self):
		c = Client(enforce_csrf_checks=True)
		r = c.get(reverse('login'))
		tok = r.cookies['csrftoken'].value if 'csrftoken' in r.cookies else c.cookies['csrftoken'].value
		c.post(reverse('login'), {'username': 'adm@teste.tl', 'password': PASSWORD, 'csrfmiddlewaretoken': tok})
		tok_tab1 = c.cookies['csrftoken'].value                     # token iha pájina tab tuan
		c.get(reverse('login') + '?tab=1')
		r = c.post(reverse('login'), {'username': 'adm@teste.tl', 'password': PASSWORD, 'tab': '1', 'csrfmiddlewaretoken': tok_tab1})
		self.assertEqual(r.status_code, 302)
		self.assertEqual(c.cookies['csrftoken'].value, tok_tab1)     # token la troka
		r = c.post(reverse('logout'), {'csrfmiddlewaretoken': tok_tab1})   # tab tuan: logout
		self.assertEqual(r.status_code, 302)

	def test_pajina_csrf_amigavel(self):
		c = Client(enforce_csrf_checks=True)
		r = c.post(reverse('login'), {'username': 'x@teste.tl', 'password': 'x'})
		self.assertEqual(r.status_code, 403)
		self.assertContains(r, 'RbR-CSRF', status_code=403)
