from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from config.rbac import ADMIN, SUPERADMIN, INVESTIGADOR, ANALISTA
from config.testing import setup_master, make_user, PASSWORD
from users.models import Pesoal, PesoalUser, OfflinePermission
from users.tasks import check_offline_permission
from users.validators import NotDefaultPasswordValidator


class LoginTest(TestCase):
	def setUp(self):
		setup_master()
		self.user = make_user(ADMIN, email='joana@teste.tl')

	def test_login_ho_email_la_haree_letra_boot(self):
		r = self.client.post(reverse('login'), {'username': 'JOANA@teste.tl', 'password': PASSWORD})
		self.assertRedirects(r, reverse('home'))

	def test_login_sala_hatudu_erru(self):
		r = self.client.post(reverse('login'), {'username': 'joana@teste.tl', 'password': 'sala'})
		self.assertEqual(r.status_code, 200)
		self.assertFalse(r.wsgi_request.user.is_authenticated)

	@override_settings(AXES_FAILURE_LIMIT=3)
	def test_konta_xave_hafoin_sala_barak(self):
		for _ in range(3):
			self.client.post(reverse('login'), {'username': 'joana@teste.tl', 'password': 'sala'})
		r = self.client.post(reverse('login'), {'username': 'joana@teste.tl', 'password': PASSWORD})
		self.assertEqual(r.status_code, 429)

	def test_pajina_login_redirect_se_login_ona(self):
		self.client.force_login(self.user)
		self.assertRedirects(self.client.get(reverse('login')), reverse('home'))


class ForceChangePasswordTest(TestCase):
	def setUp(self):
		setup_master()
		self.user = make_user(INVESTIGADOR, must_change=True, password=settings.DEFAULT_PASSWORD)
		self.client.force_login(self.user)

	def test_tenke_troka_password_uluk(self):
		self.assertRedirects(self.client.get(reverse('home')), reverse('user-change-password'))

	def test_troka_password_libera_asesu(self):
		r = self.client.post(reverse('user-change-password'), {
			'old_password': settings.DEFAULT_PASSWORD, 'new_password1': 'Lafaek#Terrenu-77', 'new_password2': 'Lafaek#Terrenu-77'})
		self.assertRedirects(r, reverse('user-change-password-done'))
		self.assertFalse(PesoalUser.objects.get(user=self.user).must_change_password)
		self.assertEqual(self.client.get(reverse('home')).status_code, 200)

	def test_labele_uza_password_default_fali(self):
		r = self.client.post(reverse('user-change-password'), {
			'old_password': settings.DEFAULT_PASSWORD, 'new_password1': settings.DEFAULT_PASSWORD, 'new_password2': settings.DEFAULT_PASSWORD})
		self.assertEqual(r.status_code, 200)
		self.assertTrue(PesoalUser.objects.get(user=self.user).must_change_password)


class RBACTest(TestCase):
	def setUp(self):
		setup_master()

	def test_investigador_no_analista_labele_jere_utilizador(self):
		for role in (INVESTIGADOR, ANALISTA):
			self.client.force_login(make_user(role))
			self.assertEqual(self.client.get(reverse('pesoal-list')).status_code, 403)

	def test_utilizador_la_iha_group_la_500(self):
		u = User.objects.create_user(username='sein@teste.tl', password=PASSWORD)
		self.client.force_login(u)
		self.assertEqual(self.client.get(reverse('pesoal-list')).status_code, 403)

	def test_admin_labele_edita_superadmin(self):
		sa = make_user(SUPERADMIN)
		self.client.force_login(make_user(ADMIN))
		pk = sa.pesoaluser.pesoal.pk
		self.assertEqual(self.client.get(reverse('pesoal-update', args=[pk])).status_code, 403)
		self.assertEqual(self.client.post(reverse('user-reset-password', args=[pk])).status_code, 403)

	def test_admin_labele_kria_superadmin(self):
		self.client.force_login(make_user(ADMIN))
		r = self.client.post(reverse('pesoal-add'), {'name': 'X', 'sexo': 'Mane', 'email': 'x@teste.tl', 'role': SUPERADMIN})
		self.assertEqual(r.status_code, 200)
		self.assertFalse(User.objects.filter(username='x@teste.tl').exists())


class PesoalTest(TestCase):
	def setUp(self):
		setup_master()
		self.admin = make_user(ADMIN)
		self.client.force_login(self.admin)

	def _add(self, **extra):
		data = {'name': 'Maria Soares', 'sexo': 'Feto', 'email': 'Maria@Teste.tl', 'phone': '77001122',
			'role': INVESTIGADOR, 'munisipiu': self.admin.pesoaluser.pesoal.munisipiu_id}
		data.update(extra)
		return self.client.post(reverse('pesoal-add'), data)

	def test_aumenta_kria_user_group_no_email(self):
		with self.captureOnCommitCallbacks(execute=True):
			r = self._add()
		p = Pesoal.objects.get(email='maria@teste.tl')
		self.assertRedirects(r, reverse('pesoal-detail', args=[p.pk]))
		u = p.pesoaluser.user
		self.assertEqual(u.username, 'maria@teste.tl')
		self.assertTrue(u.check_password(settings.DEFAULT_PASSWORD))
		self.assertTrue(u.groups.filter(name=INVESTIGADOR).exists())
		self.assertTrue(p.pesoaluser.must_change_password)
		self.assertTrue(u.password.startswith('argon2'))
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('maria@teste.tl', mail.outbox[0].to)

	def test_investigador_tenke_iha_munisipiu(self):
		r = self._add(munisipiu='')
		self.assertEqual(r.status_code, 200)
		self.assertFalse(Pesoal.objects.filter(email='maria@teste.tl').exists())

	def test_email_labele_duplikadu(self):
		self._add()
		r = self._add(name='Seluk')
		self.assertEqual(r.status_code, 200)
		self.assertEqual(Pesoal.objects.filter(email='maria@teste.tl').count(), 1)

	def test_reset_password(self):
		u = make_user(INVESTIGADOR)
		r = self.client.post(reverse('user-reset-password', args=[u.pesoaluser.pesoal.pk]))
		self.assertEqual(r.status_code, 302)
		u.refresh_from_db()
		self.assertTrue(u.check_password(settings.DEFAULT_PASSWORD))
		self.assertTrue(PesoalUser.objects.get(user=u).must_change_password)
		self.assertEqual(len(mail.outbox), 1)

	def test_reset_tenke_post(self):
		u = make_user(INVESTIGADOR)
		self.assertEqual(self.client.get(reverse('user-reset-password', args=[u.pesoaluser.pesoal.pk])).status_code, 405)

	def test_hapara_utilizador_kansela_offline(self):
		u = make_user(INVESTIGADOR)
		OfflinePermission.objects.create(user=u, given_by=self.admin)
		self.client.post(reverse('user-activate', args=[u.pesoaluser.pesoal.pk]))
		u.refresh_from_db()
		self.assertFalse(u.is_active)
		self.assertFalse(OfflinePermission.objects.valid().filter(user=u).exists())

	def test_labele_hapara_an_rasik(self):
		r = self.client.post(reverse('user-activate', args=[self.admin.pesoaluser.pesoal.pk]))
		self.assertEqual(r.status_code, 403)


class OfflinePermissionTest(TestCase):
	def setUp(self):
		setup_master()
		self.admin = make_user(ADMIN)
		self.inv = make_user(INVESTIGADOR)

	def test_admin_fo_autorizasaun_loron_7(self):
		self.client.force_login(self.admin)
		self.client.post(reverse('offline-give'), {'user': self.inv.pk})
		perm = OfflinePermission.objects.valid().get(user=self.inv)
		self.assertAlmostEqual((perm.end_date - perm.start_date).days, 7)
		self.assertEqual(len(mail.outbox), 1)

	def test_superadmin_labele_fo(self):
		self.client.force_login(make_user(SUPERADMIN))
		self.assertEqual(self.client.post(reverse('offline-give'), {'user': self.inv.pk}).status_code, 403)

	def test_renova_troka_antigu(self):
		p1 = OfflinePermission.objects.create(user=self.inv, given_by=self.admin)
		self.client.force_login(self.admin)
		self.client.post(reverse('offline-renew', args=[p1.pk]))
		self.assertEqual(OfflinePermission.objects.filter(user=self.inv, is_active=True).count(), 1)

	def test_task_hamate_remata(self):
		OfflinePermission.objects.create(user=self.inv, given_by=self.admin,
			start_date=timezone.now() - timedelta(days=8), end_date=timezone.now() - timedelta(days=1))
		result = check_offline_permission()
		self.assertEqual(result['expired'], 1)
		self.assertFalse(OfflinePermission.objects.filter(user=self.inv, is_active=True).exists())


class JWTTest(TestCase):
	def setUp(self):
		setup_master()
		self.admin = make_user(ADMIN)
		self.inv = make_user(INVESTIGADOR)
		self.url = reverse('api-token')

	def test_la_iha_autorizasaun_la_hetan_token(self):
		r = self.client.post(self.url, {'username': self.inv.username, 'password': PASSWORD})
		self.assertEqual(r.status_code, 400)

	def test_admin_la_hetan_token_sinkron(self):
		r = self.client.post(self.url, {'username': self.admin.username, 'password': PASSWORD})
		self.assertEqual(r.status_code, 400)

	def test_ho_autorizasaun_hetan_token_no_refresh(self):
		OfflinePermission.objects.create(user=self.inv, given_by=self.admin)
		r = self.client.post(self.url, {'username': self.inv.username.upper(), 'password': PASSWORD})
		self.assertEqual(r.status_code, 200)
		self.assertIn('offline_until', r.json())
		me = self.client.get(reverse('api-me'), HTTP_AUTHORIZATION='Bearer ' + r.json()['access'])
		self.assertEqual(me.json()['role'], INVESTIGADOR)
		ok = self.client.post(reverse('api-token-refresh'), {'refresh': r.json()['refresh']})
		self.assertEqual(ok.status_code, 200)

	def test_kansela_autorizasaun_hapara_refresh(self):
		OfflinePermission.objects.create(user=self.inv, given_by=self.admin)
		r = self.client.post(self.url, {'username': self.inv.username, 'password': PASSWORD})
		from users.services import cancel_offline
		cancel_offline(self.inv, by=self.admin)
		bad = self.client.post(reverse('api-token-refresh'), {'refresh': r.json()['refresh']})
		self.assertIn(bad.status_code, (400, 401))


class PasswordResetEmailTest(TestCase):
	def setUp(self):
		setup_master()
		self.user = make_user(INVESTIGADOR, email='ana@teste.tl')

	def test_haluha_password_haruka_email(self):
		r = self.client.post(reverse('password_reset'), {'email': 'ana@teste.tl'})
		self.assertRedirects(r, reverse('password_reset_done'))
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('/utilizador/password-reset/', mail.outbox[0].body)

	def test_email_la_rejista_la_hatudu_erru(self):
		r = self.client.post(reverse('password_reset'), {'email': 'la-iha@teste.tl'})
		self.assertRedirects(r, reverse('password_reset_done'))
		self.assertEqual(len(mail.outbox), 0)


class ValidatorLianTest(TestCase):
	def test_password_default_la_valida(self):
		with self.assertRaises(ValidationError):
			NotDefaultPasswordValidator().validate(settings.DEFAULT_PASSWORD)

	def test_troka_lian_rai_iha_konta(self):
		setup_master()
		u = make_user(ANALISTA)
		self.client.force_login(u)
		r = self.client.post(reverse('set-language'), {'language': 'pt', 'next': '/'})
		self.assertEqual(r.cookies[settings.LANGUAGE_COOKIE_NAME].value, 'pt')
		self.assertEqual(Pesoal.objects.get(pesoaluser__user=u).lian, 'pt')

	def test_next_externu_la_permite(self):
		r = self.client.post(reverse('set-language'), {'language': 'en', 'next': 'https://evil.example/'})
		self.assertEqual(r['Location'], '/')
