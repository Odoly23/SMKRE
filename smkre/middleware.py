# middleware.py
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

# URL ne'ebé la presiza "no-cache" no la rai iha session
# (PWA offline presiza cache ba static, service worker no manifest)
SKIP_PATHS = ('/static/', '/media/', '/api/', '/sw.js', '/manifest.json', '/favicon.ico')


class SecurityHeadersMiddleware(MiddlewareMixin):
	# Permissions-Policy: kamera no GPS husi SMKRE rasik deit
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
			if request.path in [reverse('login')]:
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
