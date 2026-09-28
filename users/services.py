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


def give_offline(user, by, note=''):
	# Fó (ka renova) autorizasaun offline: ida ativu deit kada utilizador
	OfflinePermission.objects.filter(user=user, is_active=True).update(is_active=False)
	perm = OfflinePermission.objects.create(user=user, given_by=by, note=note)
	logger.info(f'Autorizasaun offline fó: {user.username} to\'o {perm.end_date:%d/%m/%Y} husi {by}')
	return perm
