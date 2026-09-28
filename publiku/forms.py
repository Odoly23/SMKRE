from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from publiku.models import Publikasaun

BTN_RAI = """ <button class="btn btn-rbr" type="submit"><i class="fa fa-save"></i> {% load i18n %}{% trans "Rai" %}</button> """
MAX_MB = 20


class DateInput(forms.DateInput):
	input_type = 'date'


class PublikasaunForm(forms.ModelForm):
	class Meta:
		model = Publikasaun
		fields = ['tipu', 'titulu', 'lian', 'data', 'file', 'rezumu']
		widgets = {
			'data': DateInput(),
			'rezumu': forms.Textarea(attrs={'rows': 4, 'maxlength': 600}),
		}

	def __init__(self, *args, **kwargs):
		super(PublikasaunForm, self).__init__(*args, **kwargs)
		self.fields['file'].widget.attrs.update({'accept': '.pdf,application/pdf'})
		self.fields['file'].help_text = _("PDF deit · máximu 20 MB")
		self.helper = FormHelper()
		self.helper.form_tag = False          # <form> iha template (pola form.html)
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('tipu', css_class='form-group col-md-4 mb-0'),
				Column('lian', css_class='form-group col-md-4 mb-0'),
				Column('data', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			'titulu',
			'file',
			'rezumu',
			HTML(BTN_RAI)
		)

	def clean_file(self):
		f = self.cleaned_data.get('file')
		if f and hasattr(f, 'read') and not getattr(f, '_committed', False):
			if f.size > MAX_MB * 1024 * 1024:
				raise forms.ValidationError(_('File boot liu. Máximu %(mb)s MB.') % {'mb': MAX_MB})
			f.seek(0)
			if not f.read(5).startswith(b'%PDF'):
				raise forms.ValidationError(_('File tenke PDF loos.'))
			f.seek(0)
		return f
