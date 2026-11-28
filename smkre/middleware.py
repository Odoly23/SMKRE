# middleware.py
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

# URL ne'ebé la presiza "no-cache" no la rai iha session
# (PWA offline presiza cache ba static, service worker no manifest)
SKIP_PATHS = ('/static/', '/media/', '/api/', '/sw.js', '/manifest.json', '/favicon.ico')


class SecurityHeadersMiddleware(MiddlewareMixin):
	# Permissions-Policy: kamera no GPS husi SIBAR-RbR rasik deit
	def process_response(self, request, response):
		response.setdefault('Permissions-Policy', settings.PERMISSIONS_POLICY)
		return response


class PreviousURLMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		# Rai URL anterior iha session (pájina normál deit, la'ós API / static)
		if not request.path.startswith(SKIP_PATHS) and hasattr(request, 'session'):
			referer = request.META.get('HTTP_REFERER', None)
			if request.session.get('previous_url') != referer:
				request.session['previous_url'] = referer
		response = self.get_response(request)
		return response


class NoBackAfterLogout(MiddlewareMixin):
	def process_view(self, request, view_func, view_args, view_kwargs):
		# Se login ona, labele fila ba pájina login
		if request.user.is_authenticated:
			tab = request.GET.get('tab') or request.POST.get('tab')      # tab foun: husu password fali
			if request.path in [reverse('login')] and not tab:
				return redirect('home')
		return None

	def process_response(self, request, response):
		# Pájina ho login deit mak la bele rai iha cache (butaun "back")
		if not request.path.startswith(SKIP_PATHS):
			response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
			response['Pragma'] = 'no-cache'
			response['Expires'] = '0'
		return response


class ForceChangePasswordMiddleware(MiddlewareMixin):
	# Utilizador foun ka hafoin reset → tenke troka password uluk antes uza sistema
	ALLOWED_NAMES = ('user-change-password', 'user-change-password-done', 'logout', 'set-language')

	def process_view(self, request, view_func, view_args, view_kwargs):
		user = request.user
		if not user.is_authenticated or request.path.startswith(SKIP_PATHS):
			return None
		pu = getattr(user, 'pesoaluser', None)
		if pu and pu.must_change_password:
			match = request.resolver_match
			if match and match.url_name in self.ALLOWED_NAMES:
				return None
			return redirect('user-change-password')
		return None



# Sesaun web ida de'it kada utilizador: sesaun ne'ebé la'ós ativu ona (dispozitivu seluk tama / Admin hamoos) → sai.
# Atualiza "last_seen" (máximu dala ida kada minutu) atu sesaun la ativu bele troka.
class SesaunUnikuMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		user = getattr(request, 'user', None)
		sk = request.session.session_key if hasattr(request, 'session') else None
		if user is not None and user.is_authenticated and sk:
			from django.contrib import messages
			from django.contrib.auth import logout
			from django.utils import timezone
			from django.utils.translation import gettext as _
			from users.models import SesaunAtivu
			from users.sesaun import rejista, TOKEN
			rec = SesaunAtivu.objects.filter(user=user).first()
			token = request.session.get(TOKEN)
			agora = timezone.now()
			if rec is None or token is None:             # sesaun uluk deploy (la iha token): rejista
				rejista(user, request)
			elif rec.token != token:                     # dispozitivu seluk tama / Admin taka sesaun
				logout(request)
				messages.warning(request, _('Sesaun remata: konta ne\'e login iha dispozitivu seluk ka Admin taka sesaun.'))
				return redirect('login')
			elif rec.session_key != sk or (agora - rec.last_seen).total_seconds() > 60:
				SesaunAtivu.objects.filter(pk=rec.pk).update(last_seen=agora, session_key=sk)   # troka password → session_key foun
		return self.get_response(request)
