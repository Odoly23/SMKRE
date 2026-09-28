from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from users.models import OfflinePermission
from notification.utils import kirim_notif


@shared_task
def check_offline_permission():
	# Knaar kada loron (Celery Beat): hamate autorizasaun remata + lembrete loron ida antes
	now = timezone.now()
	expired = OfflinePermission.objects.filter(is_active=True, end_date__lte=now)
	n_expired = expired.update(is_active=False)
	n_remind = 0
	for perm in OfflinePermission.objects.filter(is_active=True, end_date__gt=now, end_date__lte=now + timedelta(days=1)).select_related('user'):
		kirim_notif(perm.user, 'OFFLINE', 'Autorizasaun offline remata aban. Kontaktu Admin atu renova.', url='/', email=True)
		n_remind += 1
	return {'expired': n_expired, 'remind': n_remind}
