import logging
import re
from django.conf import settings
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from config.utils import get_client_ip
from users.auth_utils import c_user_group, c_user_pesoal
from users.forms import EmailLoginForm, AccountForm, ChangePasswordForm
from users.models import PesoalUser

logger = logging.getLogger('smkre.seguransa')


def _set_lang_cookie(response, lang):
	if lang in dict(settings.LANGUAGES):
		response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, max_age=settings.LANGUAGE_COOKIE_AGE,
			samesite='Lax', secure=not settings.DEBUG)
	return response


# limite tentativa login kada IP (hotu, loos ka sala) — protesaun extra liu axes (axes: username + IP)
LOGIN_IP_LIMITE = 20
LOGIN_IP_MINUTU = 10


# testu ba log: hamoos karakter kontrolu/liña foun (anti log injection), badak
def _log_seguru(t):
	return re.sub(r'[\x00-\x1f\x7f]', '?', str(t or ''))[:80]


# login staf iha /Tama-Lai/ (la iha link públiku). Kamada protesaun:
# CSRF · limite IP · axes (xave konta sala dala 5) · honeypot · validasaun formuláriu · ORM (anti SQLi) ·
# erru jeral (la fó sai email iha ka lae) · never_cache · noindex · log seguransa
class UserLoginView(auth_views.LoginView):
	template_name = 'auth/login.html'
	authentication_form = EmailLoginForm
	redirect_authenticated_user = True

	# tab foun (?tab=1): utilizador login ona iha browser ne'e, maibé tab foun tenke hatama password fali
	def modu_tab(self):
		return self.request.user.is_authenticated and bool(self.request.GET.get('tab') or self.request.POST.get('tab'))

	def dispatch(self, request, *args, **kwargs):
		if self.modu_tab():
			self.redirect_authenticated_user = False
		return super().dispatch(request, *args, **kwargs)

	def get_initial(self):
		ini = super().get_initial()
		if self.modu_tab():
			ini['username'] = self.request.user.username
		return ini

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx['modu_tab'] = self.modu_tab()
		return ctx

	# hafoin login: URL ho ID tab foun (_tab) → tab_sesaun.js rai iha sessionStorage
	def get_success_url(self):
		url = super().get_success_url()
		tab = getattr(self, '_tab', None)
		return url + ('&' if '?' in url else '?') + '_tab=' + tab if tab else url

	# POST: konta tentativa kada IP; liu limite → 429 (antes kalkula password)
	def post(self, request, *args, **kwargs):
		ip = get_client_ip(request) or 'la-hatene'
		chave = f'login-ip:{ip}'
		cache.add(chave, 0, LOGIN_IP_MINUTU * 60)
		try:
			n = cache.incr(chave)
		except ValueError:
			cache.set(chave, 1, LOGIN_IP_MINUTU * 60)
			n = 1
		if n > LOGIN_IP_LIMITE:
			logger.warning(f'Login: IP {_log_seguru(ip)} liu limite ({n} tentativa / {LOGIN_IP_MINUTU} min)')
			return render(request, 'home/lockout.html', status=429)
		return super().post(request, *args, **kwargs)

	# login loos: log + lian utilizador
	def form_valid(self, form):
		from users import sesaun
		user = form.get_user()
		if self.modu_tab():
			if user.pk != self.request.user.pk:
				form.add_error(None, _('Tab ne\'e iha sesaun husi utilizador seluk. Logout uluk.'))
				return self.form_invalid(form)
			# tab foun, utilizador hanesan: password loos → ID tab foun de'it. LA login() fali:
			# login() troka token CSRF → formuláriu iha tab tuan sei falla (403 CSRF).
			from django.http import HttpResponseRedirect
			self._tab = sesaun.tab_foun(self.request)
			logger.info(f'Tab foun: {user.username} IP {get_client_ip(self.request)}')
			return HttpResponseRedirect(self.get_success_url())
		rec = sesaun.sesaun_seluk(user, self.request)
		if rec:                                      # login ida de'it: dispozitivu seluk sei ativu
			logger.warning(f'Login bloka (sesaun ativu iha dispozitivu seluk): {user.username} IP {get_client_ip(self.request)}')
			form.add_error(None, _('Konta ne\'e login hela iha dispozitivu seluk (%(d)s, IP %(ip)s, ativu ikus %(t)s). Logout uluk iha dispozitivu ne\'e, ka kontaktu Admin atu taka sesaun.') % {
				'd': rec.dispozitivu, 'ip': rec.ip or '-', 't': timezone.localtime(rec.last_seen).strftime('%d/%m/%Y %H:%M')})
			return self.form_invalid(form)
		response = super().form_valid(form)        # login() → session_key foun
		sesaun.rejista(user, self.request)
		self._tab = sesaun.tab_foun(self.request)
		response['Location'] = self.get_success_url()
		logger.info(f'Login: {user.username} IP {get_client_ip(self.request)}')
		pesoal = c_user_pesoal(user)
		if pesoal:
			_set_lang_cookie(response, pesoal.lian)
		return response

	# login sala: log seguransa (email limpu, la rai password)
	def form_invalid(self, form):
		logger.warning(f'Login sala: {_log_seguru(self.request.POST.get("username"))} IP {_log_seguru(get_client_ip(self.request))}')
		return super().form_invalid(form)

	# pájina login la tama iha Google / motor buka
	def render_to_response(self, context, **kwargs):
		response = super().render_to_response(context, **kwargs)
		response['X-Robots-Tag'] = 'noindex, nofollow'
		return response


class UserLogoutView(auth_views.LogoutView):
	# Django 5: logout tenke POST (seguru hasoru CSRF)
	pass


@login_required
def AccountUpdate(request):
	group = c_user_group(request.user)
	pesoal = c_user_pesoal(request.user)
	if not pesoal:
		messages.warning(request, _('Konta ne\'e seidauk iha dadus pesoal. Kontaktu Admin.'))
		return redirect('home')
	if request.method == 'POST':
		form = AccountForm(request.POST, request.FILES, instance=pesoal)
		if form.is_valid():
			instance = form.save()
			messages.success(request, _('Ita-nia konta atualiza ona!'))
			return _set_lang_cookie(redirect('user-account'), instance.lian)
	else:
		form = AccountForm(instance=pesoal)
	context = {
		'group': group, "page": "account", 'form': form,
		'title': _('Konta'), 'legend': _('Ha\'u-nia Konta'),
	}
	return render(request, 'auth/account.html', context)


class UserPasswordChangeView(auth_views.PasswordChangeView):
	form_class = ChangePasswordForm
	template_name = 'auth/change_password.html'
	success_url = reverse_lazy('user-change-password-done')

	def form_valid(self, form):
		response = super().form_valid(form)
		PesoalUser.objects.filter(user=self.request.user).update(must_change_password=False)
		logger.info(f'Troka password: {self.request.user.username}')
		return response


class UserPasswordChangeDoneView(auth_views.PasswordChangeDoneView):
	template_name = 'auth/change_password_done.html'


class UserPasswordResetView(auth_views.PasswordResetView):
	template_name = 'auth/password_reset.html'
	email_template_name = 'auth/email/password_reset_email.txt'
	html_email_template_name = 'auth/email/password_reset_email.html'
	subject_template_name = 'auth/email/password_reset_subject.txt'
	success_url = reverse_lazy('password_reset_done')
	extra_email_context = {'site_url': settings.SITE_URL}


class UserPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
	template_name = 'auth/password_reset_confirm.html'
	success_url = reverse_lazy('password_reset_complete')

	def form_valid(self, form):
		response = super().form_valid(form)
		PesoalUser.objects.filter(user=form.user).update(must_change_password=False)
		logger.info(f'Reset password liuhusi email: {form.user.username}')
		return response
