from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from config.rbac import INVESTIGADOR, roles_admin_can_assign
from custom.models import Munisipiu, Pozisaun
from users.models import Pesoal, OfflinePermission

BTN_RAI = """ <button class="btn btn-rbr" type="submit"><i class="fa fa-save"></i> {% load i18n %}{% trans "Rai" %}</button> """


class EmailLoginForm(AuthenticationForm):
	username = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email', 'placeholder': 'naran@redebarai.org'}))
	password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

	def clean_username(self):
		return self.cleaned_data['username'].strip().lower()


class PesoalForm(forms.ModelForm):
	role = forms.ChoiceField(label=_("Papél (Role)"), choices=[])

	class Meta:
		model = Pesoal
		fields = ['name', 'sexo', 'email', 'phone', 'pos', 'munisipiu', 'image']

	def __init__(self, *args, **kwargs):
		admin_group = kwargs.pop('admin_group', None)
		initial_role = kwargs.pop('initial_role', None)
		super(PesoalForm, self).__init__(*args, **kwargs)
		self.fields['role'].choices = [('', '---------')] + list(roles_admin_can_assign(admin_group))
		if initial_role:
			self.fields['role'].initial = initial_role
		self.fields['pos'].queryset = Pozisaun.active.all()
		self.fields['munisipiu'].queryset = Munisipiu.active.all()
		self.fields['munisipiu'].help_text = _("Obrigatóriu ba Investigadór")
		self.helper = FormHelper()
		self.helper.form_tag = False          # <form> iha template (pola form.html)
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('name', css_class='form-group col-md-6 mb-0'),
				Column('sexo', css_class='form-group col-md-3 mb-0'),
				Column('phone', css_class='form-group col-md-3 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('email', css_class='form-group col-md-6 mb-0'),
				Column('role', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('pos', css_class='form-group col-md-4 mb-0'),
				Column('munisipiu', css_class='form-group col-md-4 mb-0'),
				Column('image', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			HTML(BTN_RAI)
		)

	def clean_email(self):
		email = self.cleaned_data['email'].strip().lower()
		qs = User.objects.filter(username__iexact=email)
		if self.instance.pk and hasattr(self.instance, 'pesoaluser') and self.instance.pesoaluser.user:
			qs = qs.exclude(pk=self.instance.pesoaluser.user.pk)
		if qs.exists():
			raise forms.ValidationError(_("Email ne'e uza ona husi utilizador seluk."))
		return email

	def clean(self):
		cleaned = super().clean()
		if cleaned.get('role') == INVESTIGADOR and not cleaned.get('munisipiu'):
			self.add_error('munisipiu', _("Investigadór tenke iha munisípiu knaar."))
		return cleaned


class AccountForm(forms.ModelForm):
	# Utilizador atualiza nia konta rasik (email/role labele muda iha ne'e)
	class Meta:
		model = Pesoal
		fields = ['name', 'sexo', 'phone', 'lian', 'image']

	def __init__(self, *args, **kwargs):
		super(AccountForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('name', css_class='form-group col-md-6 mb-0'),
				Column('sexo', css_class='form-group col-md-3 mb-0'),
				Column('phone', css_class='form-group col-md-3 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('lian', css_class='form-group col-md-6 mb-0'),
				Column('image', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			HTML(BTN_RAI)
		)


class ChangePasswordForm(PasswordChangeForm):
	def __init__(self, *args, **kwargs):
		super(ChangePasswordForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			'old_password', 'new_password1', 'new_password2',
			HTML(""" {% load i18n %}<button class="btn btn-rbr btn-block" type="submit"><i class="fa fa-key"></i> {% trans "Troka Password" %}</button> """)
		)


class OfflinePermissionForm(forms.ModelForm):
	class Meta:
		model = OfflinePermission
		fields = ['user', 'note']

	def __init__(self, *args, **kwargs):
		super(OfflinePermissionForm, self).__init__(*args, **kwargs)
		self.fields['user'].queryset = User.objects.filter(groups__name=INVESTIGADOR, is_active=True).order_by('username')
		self.fields['user'].label_from_instance = lambda u: f'{getattr(getattr(u, "pesoaluser", None), "pesoal", None) or u.username} ({u.username})'
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('user', css_class='form-group col-md-6 mb-0'),
				Column('note', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			HTML(""" {% load i18n %}<button class="btn btn-rbr" type="submit"><i class="fa fa-check"></i> {% trans "Fó Autorizasaun" %}</button> """)
		)
