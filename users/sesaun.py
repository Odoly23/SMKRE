"""Login ida de'it kada utilizador + tab foun tenke login fali.

1. Dispozitivu ida: konta login hela iha dispozitivu A → login iha B rejeita to'o A logout.
   Sesaun A la ativu liu minutu SESAUN_IDLE_MINUTU (ex. taka browser la logout) → B bele tama; A sai automátiku.
   Admin / Superadmin bele hamoos sesaun ativu (detalla utilizador).
2. Tab: kada tab browser iha ID rasik (sessionStorage). Tab foun / link kopia → husu password fali
   (main/static/main/js/tab_sesaun.js + meta "sibar-tab" iha layout).
App offline (token JWT) la afeta."""
import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from config.utils import get_client_ip

TAB_MAX = 10


def idle():
	return timedelta(minutes=getattr(settings, 'SESAUN_IDLE_MINUTU', 30))


TOKEN = 'sesaun_id'


# sesaun iha dispozitivu SELUK ne'ebé sei ativu (ka None)
def sesaun_seluk(user, request):
	from users.models import SesaunAtivu
	rec = SesaunAtivu.objects.filter(user=user).first()
	if not rec or rec.token == request.session.get(TOKEN):
		return None
	if rec.last_seen < timezone.now() - idle():
		return None
	if not Session.objects.filter(session_key=rec.session_key, expire_date__gt=timezone.now()).exists():
		return None
	return rec


# rejista sesaun foun (hafoin login); sesaun tuan (la ativu) sai
def rejista(user, request):
	from users.models import SesaunAtivu
	token = request.session.get(TOKEN) or secrets.token_urlsafe(24)
	request.session[TOKEN] = token
	if not request.session.session_key:
		request.session.save()
	tuan = SesaunAtivu.objects.filter(user=user).exclude(token=token).first()
	if tuan and tuan.session_key != request.session.session_key:
		Session.objects.filter(session_key=tuan.session_key).delete()
	SesaunAtivu.objects.update_or_create(user=user, defaults={
		'session_key': request.session.session_key, 'token': token, 'ip': get_client_ip(request) or None,
		'user_agent': (request.META.get('HTTP_USER_AGENT') or '')[:255], 'last_seen': timezone.now()})


# hamoos sesaun ativu (logout ka Admin hamoos)
def hamoos(user, session_key=None):
	from users.models import SesaunAtivu
	qs = SesaunAtivu.objects.filter(user=user)
	if session_key:
		qs = qs.filter(session_key=session_key)
	for rec in qs:
		Session.objects.filter(session_key=rec.session_key).delete()
	qs.delete()


# ID tab foun (rai iha sesaun; tab ida-idak hetan ID rasik hafoin login)
def tab_foun(request):
	t = secrets.token_urlsafe(12)
	request.session['tab_ids'] = (request.session.get('tab_ids', []) + [t])[-TAB_MAX:]
	return t
