from django.core import mail
from django.test import TestCase
from django.urls import reverse
from config.rbac import ADMIN, SUPERADMIN, INVESTIGADOR
from config.testing import setup_master, make_user
from notification.models import Notification
from notification.utils import kirim_notif_role


class NotificationTest(TestCase):
	def setUp(self):
		setup_master()
		self.admin = make_user(ADMIN)
		self.sa = make_user(SUPERADMIN)
		self.inv = make_user(INVESTIGADOR)

	def test_notif_ba_role_no_email(self):
		kirim_notif_role([ADMIN, SUPERADMIN], 'KAZU_FOUN', 'Kazu foun', url='/', urgent=True)
		self.assertEqual(Notification.objects.count(), 2)
		self.assertEqual(len(mail.outbox), 2)
		self.assertTrue(mail.outbox[0].subject.startswith('[URJENTE]'))

	def test_api_total_no_ikus(self):
		kirim_notif_role([ADMIN], 'KAZU_FOUN', 'Kazu A', email=False)
		self.client.force_login(self.admin)
		self.assertEqual(self.client.get('/api/notif/Notifikasaun/total/').json()['value'], 1)
		data = self.client.get('/api/notif/Notifikasaun/ikus/').json()
		self.assertEqual(data['objects'][0]['message'], 'Kazu A')

	def test_api_presiza_login(self):
		self.assertEqual(self.client.get('/api/notif/Notifikasaun/total/').status_code, 403)

	def test_loke_notif_marka_lee(self):
		n = kirim_notif_role([ADMIN], 'KAZU_FOUN', 'Kazu B', url='/', email=False)[0]
		self.client.force_login(self.admin)
		r = self.client.get(reverse('notification-open', args=[n.pk]))
		self.assertRedirects(r, '/')
		n.refresh_from_db()
		self.assertTrue(n.is_read)

	def test_labele_loke_notif_ema_seluk(self):
		n = kirim_notif_role([ADMIN], 'KAZU_FOUN', 'Kazu C', email=False)[0]
		self.client.force_login(self.inv)
		self.assertEqual(self.client.get(reverse('notification-open', args=[n.pk])).status_code, 404)

	def test_url_externu_la_redirect(self):
		n = kirim_notif_role([ADMIN], 'SISTEMA', 'X', url='https://evil.example/', email=False)[0]
		self.client.force_login(self.admin)
		self.assertRedirects(self.client.get(reverse('notification-open', args=[n.pk])), reverse('notification-list'))
