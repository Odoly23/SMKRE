import logging
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from users.models import OfflinePermission

logger = logging.getLogger('smkre.seguransa')


def revoke_tokens(user):
	# Kansela token JWT hotu (ezemplu: HP lakon, utilizador hapara, autorizasaun kansela)
	n = 0
	for token in OutstandingToken.objects.filter(user=user):
		_, created = BlacklistedToken.objects.get_or_create(token=token)
		n += int(created)
	return n


def cancel_offline(user, by=None, note=''):
	# Kansela autorizasaun offline ativu hotu ba utilizador ida
	now = timezone.now()
	n = OfflinePermission.objects.filter(user=user, is_active=True).update(
		is_active=False, cancelled_by=by, cancelled_at=now)
	revoke_tokens(user)
	if n:
		logger.info(f'Autorizasaun offline kansela: {user.username} husi {by} {note}')
	return n


def give_offline(user, by, note='', hahu=None, remata=None):
	# Fó (ka renova) autorizasaun input / offline: ida ativu deit kada utilizador.
	# hahu / remata (data): mamuk → agora to'o loron OFFLINE_PERMISSION_DAYS
	from datetime import datetime, time
	OfflinePermission.objects.filter(user=user, is_active=True).update(is_active=False)
	extra = {}
	if hahu:
		extra['start_date'] = timezone.make_aware(datetime.combine(hahu, time.min)) if hahu > timezone.localdate() else timezone.now()
	if remata:
		extra['end_date'] = timezone.make_aware(datetime.combine(remata, time.max))
	perm = OfflinePermission.objects.create(user=user, given_by=by, note=note, **extra)
	logger.info(f'Autorizasaun offline fó: {user.username} to\'o {perm.end_date:%d/%m/%Y} husi {by}')
	return perm
