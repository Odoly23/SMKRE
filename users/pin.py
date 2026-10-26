"""PIN app offline: Admin fó (ka sistema kria) bainhira fó autorizasaun offline.

Server rai hash deit (make_password). PIN uza iha app ba enkripta dadus iha HP;
server verifika PIN iha login dahuluk app nian (HP foun / dadus hamoos).
"""
import base64
import hashlib
import secrets
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

PIN_SALA_MAX = 5            # PIN sala dala 5 → xave minutu 30
PIN_XAVE_SEG = 30 * 60


def pin_fasil(pin):
	# Hanesan regra iha app: 111111, 123456, 654321…
	return len(set(pin)) == 1 or pin in '0123456789' or pin in '9876543210'


def kria_pin():
	while True:
		pin = f'{secrets.randbelow(10 ** 6):06d}'
		if not pin_fasil(pin):
			return pin


def rai_pin(user, pin):
	from users.models import PesoalUser
	PesoalUser.objects.get_or_create(user=user, defaults={'must_change_password': False})
	return PesoalUser.objects.filter(user=user).update(pin_offline=make_password(pin), pin_offline_enc=_fernet().encrypt(pin.encode()).decode(),
		pin_offline_at=timezone.now(), pin_sala=0, pin_sala_at=None)


def _fernet():
	# Xave enkriptasaun PIN husi SECRET_KEY (troka SECRET_KEY → PIN tuan labele lee; Admin fó PIN foun)
	from cryptography.fernet import Fernet
	xave = hashlib.sha256((settings.SECRET_KEY + '|smkre-pin-offline').encode()).digest()
	return Fernet(base64.urlsafe_b64encode(xave))


def lee_pin(user):
	"""PIN husi Admin (testu) ka None: seidauk iha, ka rai antes funsaun ne'e (hash de'it)."""
	pu = _pu(user)
	if not pu or not pu.pin_offline_enc:
		return None
	try:
		return _fernet().decrypt(pu.pin_offline_enc.encode()).decode()
	except Exception:
		return None


def _pu(user):
	from users.models import PesoalUser
	return PesoalUser.objects.filter(user=user).first()


def iha_pin(user):
	pu = _pu(user)
	return bool(pu and pu.pin_offline)


def pin_xave(user):
	pu = _pu(user)
	if not pu or pu.pin_sala < PIN_SALA_MAX or not pu.pin_sala_at:
		return False
	return (timezone.now() - pu.pin_sala_at).total_seconds() < PIN_XAVE_SEG


def verifika_pin(user, pin):
	"""True se PIN loos. PIN sala konta iha DB (xave minutu 30 hafoin dala PIN_SALA_MAX)."""
	from django.db.models import F
	from users.models import PesoalUser
	pu = _pu(user)
	if not pu:
		return False
	if pu.pin_offline and pin and check_password(str(pin), pu.pin_offline):
		PesoalUser.objects.filter(pk=pu.pk).update(pin_sala=0, pin_sala_at=None)
		return True
	expiradu = pu.pin_sala_at and (timezone.now() - pu.pin_sala_at).total_seconds() >= PIN_XAVE_SEG
	PesoalUser.objects.filter(pk=pu.pk).update(pin_sala=1 if expiradu else F('pin_sala') + 1, pin_sala_at=timezone.now())
	return False


def pin_se_laiha(user):
	"""Utilizador seidauk iha PIN husi Admin → kria, rai no fó PIN (ba email). Iha ona → None (PIN la muda)."""
	if iha_pin(user):
		return None
	pin = kria_pin()
	rai_pin(user, pin)
	return pin
