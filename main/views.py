import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.templatetags.static import static
from django.utils._os import safe_join
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST
from config.rbac import INVESTIGADOR, ROLE_USER_MANAGE
from users.auth_utils import c_user_group, c_user_pesoal, c_user_offline
from users.models import OfflinePermission, Pesoal


@login_required
def home(request):
	from kazu.models import DRAFT, ONGOING, PENDING, SYNCED, VERIFIED, APPROVED, REJECTED
	from kazu.permissions import kazu_queryset
	group = c_user_group(request.user)
	context = {'group': group, "page": "home", 'title': _('Varanda'), 'legend': _('Varanda')}
	qs = kazu_queryset(request.user)
	if group == INVESTIGADOR:
		context['offline'] = c_user_offline(request.user)
		context['tot_rascunho'] = qs.filter(status__in=[DRAFT, ONGOING, PENDING]).count()
		context['tot_haruka'] = qs.filter(status__in=[SYNCED, VERIFIED]).count()
		context['tot_rejeitadu'] = qs.filter(status=REJECTED).count()
		context['kazu_ikus'] = qs[:5]
		return render(request, 'home/home_investigador.html', context)
	context['tot_kazu'] = qs.exclude(status__in=[DRAFT, ONGOING, PENDING]).count()
	context['tot_synced'] = qs.filter(status=SYNCED).count()
	context['tot_verified'] = qs.filter(status=VERIFIED).count()
	context['tot_approved'] = qs.filter(status=APPROVED).count()
	context['tot_urjente'] = qs.filter(urjente=True, status__in=[SYNCED, VERIFIED, APPROVED]).count()
	# Kazu ne'ebé hein ita-nia aksaun
	if group == 'admin':
		context['hein'] = qs.filter(status=SYNCED)[:8]
	elif group == 'superadmin':
		context['hein'] = qs.filter(status__in=[SYNCED, VERIFIED])[:8]
	if group in ROLE_USER_MANAGE:
		context['tot_user'] = Pesoal.objects.count()
		context['tot_offline'] = OfflinePermission.objects.valid().count()
	return render(request, 'home/home.html', context)


@require_POST
def set_language(request):
	# Klik bandeira → troka lian; rai iha cookie no iha konta (se login)
	lang = request.POST.get('language', settings.LANGUAGE_CODE)
	next_url = request.POST.get('next') or '/'
	if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
		next_url = '/'
	response = HttpResponseRedirect(next_url)
	if lang in dict(settings.LANGUAGES):
		response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, max_age=settings.LANGUAGE_COOKIE_AGE,
			samesite='Lax', secure=not settings.DEBUG)
		if request.user.is_authenticated:
			pesoal = c_user_pesoal(request.user)
			if pesoal:
				Pesoal.objects.filter(pk=pesoal.pk).update(lian=lang)
	return response


@cache_control(max_age=3600)
def manifest(request):
	# PWA manifest (instala SMKRE iha HP)
	return JsonResponse({
		'name': 'SMKRE — Rede ba Rai',
		'short_name': 'SMKRE',
		'description': 'Sistema Monitorizasaun Konflitu Rai no Eviksaun',
		'start_url': '/',
		'scope': '/',
		'display': 'standalone',
		'orientation': 'portrait',
		'background_color': '#F4F5F1',
		'theme_color': '#0E8A68',
		'lang': 'tet',
		'shortcuts': [{'name': 'SMKRE Offline', 'short_name': 'Offline', 'url': '/sinkron/'}],
		'icons': [
			{'src': static('main/images/icon-192.png'), 'sizes': '192x192', 'type': 'image/png'},
			{'src': static('main/images/icon-512.png'), 'sizes': '512x512', 'type': 'image/png'},
			{'src': static('main/images/icon-512-maskable.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
		],
	}, content_type='application/manifest+json')


# Aset ne'ebé service worker rai iha cache (app offline). URL husi static() → loos mós ho naran hash (production).
SW_ASSETS = [
	'main/css/bootstrap.min.css', 'main/css/main.css', 'main/css/fonts.css',
	'main/font-awesome/css/font-awesome.min.css', 'main/font-awesome/fonts/fontawesome-webfont.woff2',
	'main/js/jquery.min.js', 'main/js/bootstrap.bundle.min.js', 'main/js/main.js',
	'main/images/logo.png', 'main/images/favicon.png', 'main/images/icon-192.png',
	'main/fonts/lato-latin-400-normal.woff2', 'main/fonts/lato-latin-700-normal.woff2',
	'main/fonts/montserrat-latin-700-normal.woff2',
	'main/offline/offline.css', 'main/offline/smkre_kripto.js', 'main/offline/smkre_db.js',
	'main/offline/smkre_kamera.js', 'main/offline/smkre_offline.js',
]


@cache_control(no_cache=True)
def service_worker(request):
	# Service worker tenke serve husi raiz "/" atu kontrola pájina hotu.
	# Lista aset + versaun cache hatama iha ne'e: aset muda → hash muda → cache foun automátiku.
	import hashlib, json
	assets = [static(a) for a in SW_ASSETS]
	versaun = hashlib.sha256('|'.join(assets).encode()).hexdigest()[:10]
	path = settings.BASE_DIR / 'main' / 'static' / 'main' / 'pwa' / 'sw.js'
	js = path.read_text(encoding='utf-8').replace("'__SW_VERSAUN__'", json.dumps(versaun)).replace("'__SW_ASSETS__'", json.dumps(assets))
	response = HttpResponse(js, content_type='application/javascript')
	response['Service-Worker-Allowed'] = '/'
	return response


@login_required
def protected_media(request, path):
	# Media LA serve direta husi Nginx: tenke login + asesu ba kazu (evidénsia)
	if path.startswith('kazu/'):
		from kazu.models import Kazu
		from kazu.permissions import can_view
		kazu = Kazu.objects.filter(pk=path.split('/')[1]).first() if path.count('/') >= 2 else None
		if not kazu or not can_view(request.user, kazu):
			raise Http404
	elif not path.startswith('pesoal/'):
		raise Http404
	try:
		full = safe_join(settings.MEDIA_ROOT, path)
	except Exception:
		raise Http404
	if not os.path.isfile(full):
		raise Http404
	response = FileResponse(open(full, 'rb'))
	response['Cache-Control'] = 'private, max-age=3600'
	response['X-Content-Type-Options'] = 'nosniff'
	return response


def offline_page(request):
	return render(request, 'home/offline.html', {'title': 'Offline'})


def error_403(request, exception=None):
	return render(request, 'home/403.html', status=403)


def error_404(request, exception=None):
	return render(request, 'home/404.html', status=404)


def error_500(request):
	return render(request, 'home/500.html', status=500)
