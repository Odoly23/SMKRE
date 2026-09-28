from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from kazu.models import Kazu
from legal.models import DokumentuLegal, NotaLegal
from legal.services import KAZU_STATUS_LEGAL

BTN_RAI = """ <button class="btn btn-rbr" type="submit"><i class="fa fa-save"></i> {% load i18n %}{% trans "Rai" %}</button> """
ACCEPT = '.pdf,.jpg,.jpeg,.png,.docx,application/pdf,image/jpeg,image/png'


class DateInput(forms.DateInput):
	input_type = 'date'


class DokumentuForm(forms.ModelForm):
	class Meta:
		model = DokumentuLegal
		fields = ['kazu', 'kategoria', 'titulu', 'data_dokumentu', 'file', 'deskrisaun', 'konfidensial']
		widgets = {
			'data_dokumentu': DateInput(),
			'deskrisaun': forms.Textarea(attrs={'rows': 3}),
		}

	def __init__(self, *args, **kwargs):
		kazu = kwargs.pop('kazu', None)
		super(DokumentuForm, self).__init__(*args, **kwargs)
		# Kazu verifikadu deit; se upload husi pájina kazu → kazu fixu
		self.fields['kazu'].queryset = Kazu.objects.filter(status__in=KAZU_STATUS_LEGAL).order_by('-created_at')
		if kazu:
			self.fields['kazu'].queryset = Kazu.objects.filter(pk=kazu.pk)
			self.fields['kazu'].initial = kazu.pk
			self.fields['kazu'].disabled = True
		self.fields['file'].widget.attrs.update({'accept': ACCEPT})
		self.fields['file'].help_text = _("PDF, JPG, PNG ka DOCX · máximu 20 MB")
		self.helper = FormHelper()
		self.helper.form_tag = False          # <form> iha template (pola form.html)
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('kazu', css_class='form-group col-md-6 mb-0'),
				Column('kategoria', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('titulu', css_class='form-group col-md-8 mb-0'),
				Column('data_dokumentu', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('file', css_class='form-group col-md-8 mb-0'),
				Column('konfidensial', css_class='form-group col-md-4 mb-0 pt-md-4'),
				css_class='form-row'
			),
			'deskrisaun',
			HTML(BTN_RAI)
		)


class VersaunForm(forms.Form):
	file = forms.FileField(label=_("File versaun foun"), help_text=_("PDF, JPG, PNG ka DOCX · máximu 20 MB"))
	deskrisaun = forms.CharField(label=_("Saida mak muda?"), required=False, widget=forms.Textarea(attrs={'rows': 2}))

	def __init__(self, *args, **kwargs):
		super(VersaunForm, self).__init__(*args, **kwargs)
		self.fields['file'].widget.attrs.update({'accept': ACCEPT})
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			'file',
			'deskrisaun',
			HTML(BTN_RAI)
		)


class NotaForm(forms.ModelForm):
	class Meta:
		model = NotaLegal
		fields = ['tipu', 'prazu', 'testu', 'konfidensial', 'remata']
		widgets = {
			'prazu': DateInput(),
			'testu': forms.Textarea(attrs={'rows': 5}),
		}

	def __init__(self, *args, **kwargs):
		super(NotaForm, self).__init__(*args, **kwargs)
		if not self.instance.pk:
			del self.fields['remata']
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('tipu', css_class='form-group col-md-6 mb-0'),
				Column('prazu', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			'testu',
			Row(
				Column('konfidensial', css_class='form-group col-md-6 mb-0'),
				Column('remata', css_class='form-group col-md-6 mb-0') if 'remata' in self.fields else HTML(''),
				css_class='form-row'
			),
			HTML(BTN_RAI)
		)
