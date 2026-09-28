import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
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


class UserLoginView(auth_views.LoginView):
	template_name = 'auth/login.html'
	authentication_form = EmailLoginForm
	redirect_authenticated_user = True

	def form_valid(self, form):
		response = super().form_valid(form)
		user = form.get_user()
		logger.info(f'Login: {user.username} IP {get_client_ip(self.request)}')
		pesoal = c_user_pesoal(user)
		if pesoal:
			_set_lang_cookie(response, pesoal.lian)
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
