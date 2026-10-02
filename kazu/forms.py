from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Field
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia, TipuKonflitu, TipuRai, \
	TipuEviksaun, TipuAtor, EstraguPatrimoniu, NesesidadeUrjente
from kazu.models import Kazu, UmaKainAfetada, InsidenteEviksaun, AtorEnvolvidu, Evidensia, STATUS_KAZU_CHOICES

# Limite territóriu Timor-Leste (inklui Oé-Cusse no Ataúro)
TL_LAT = (Decimal('-9.60'), Decimal('-8.10'))
TL_LON = (Decimal('124.00'), Decimal('127.40'))
GPS_MAX_AKURASIA = 50


class DateInput(forms.DateInput):
	input_type = 'date'


# Títulu seksaun formuláriu (lista ne'e atu tools/extract_lian.py hetan testu ba tradusaun)
SECTION_TITLES = [_('Identifikasaun no Fatin'), _('Informasaun Insidente'), _('Atór Envolvidu no Populasaun Afetada'),
	_('Estragu Patrimóniu'), _('Evidénsia'), _('Nesesidade Urjente no Konsentimentu')]


def section(num, title):
	return HTML(f""" {{% load i18n %}}<h3 class="form-section"><span>{num}</span> {{% trans "{title}" %}}</h3> """)


class KazuForm(forms.ModelForm):
	data_relatoriu = forms.DateField(label=_("Data Relatóriu"), widget=DateInput(), required=True, initial=timezone.localdate)
	data_akontesimentu = forms.DateField(label=_("Data Akontesimentu"), widget=DateInput(), required=False)

	class Meta:
		model = Kazu
		fields = ['titulu', 'data_relatoriu', 'munisipiu', 'postu', 'suku', 'aldeia',
			'latitude', 'longitude', 'gps_akurasia',
			'data_akontesimentu', 'tipu_konflitu', 'tipu_seluk', 'tipu_rai', 'deskrisaun',
			'estragu', 'estragu_seluk', 'nesesidade', 'konsentimentu', 'la_publika', 'observasaun']
		widgets = {
			'tipu_konflitu': forms.CheckboxSelectMultiple,
			'estragu': forms.CheckboxSelectMultiple,
			'nesesidade': forms.CheckboxSelectMultiple,
			'deskrisaun': forms.Textarea(attrs={'rows': 4, 'placeholder': _('Deskreve badak saida mak akontese, inklui sekuénsia akontesimentu, asaun husi autoridade ka atór no impaktu ba komunidade.')}),
			'observasaun': forms.Textarea(attrs={'rows': 2}),
			'latitude': forms.NumberInput(attrs={'readonly': True, 'step': 'any'}),
			'longitude': forms.NumberInput(attrs={'readonly': True, 'step': 'any'}),
			'gps_akurasia': forms.NumberInput(attrs={'readonly': True}),
		}

	def __init__(self, *args, **kwargs):
		self.munisipiu_knaar = kwargs.pop('munisipiu_knaar', None)
		self.submit = kwargs.pop('submit', False)
		super(KazuForm, self).__init__(*args, **kwargs)
		self.fields['tipu_konflitu'].queryset = TipuKonflitu.active.all()
		self.fields['tipu_rai'].queryset = TipuRai.active.all()
		self.fields['estragu'].queryset = EstraguPatrimoniu.active.all()
		self.fields['nesesidade'].queryset = NesesidadeUrjente.active.all()

		# Investigadór: munisípiu knaar deit (la bele muda)
		if self.munisipiu_knaar:
			self.fields['munisipiu'].queryset = Munisipiu.objects.filter(pk=self.munisipiu_knaar.pk)
			self.fields['munisipiu'].initial = self.munisipiu_knaar.pk
			self.fields['munisipiu'].disabled = True
		else:
			self.fields['munisipiu'].queryset = Munisipiu.active.all()

		# Dropdown bertingkat (hanesan FunsFormAddress)
		self.fields['postu'].queryset = PostuAdministrativu.objects.none()
		self.fields['suku'].queryset = Suku.objects.none()
		self.fields['aldeia'].queryset = Aldeia.objects.none()
		munisipiu_id = self.munisipiu_knaar.pk if self.munisipiu_knaar else None
		if 'munisipiu' in self.data and not self.munisipiu_knaar:
			try:
				munisipiu_id = int(self.data.get('munisipiu'))
			except (ValueError, TypeError):
				pass
		elif self.instance.pk and self.instance.munisipiu_id:
			munisipiu_id = self.instance.munisipiu_id
		if munisipiu_id:
			self.fields['postu'].queryset = PostuAdministrativu.active.filter(munisipiu_id=munisipiu_id).order_by('name')

		if 'postu' in self.data:
			try:
				self.fields['suku'].queryset = Suku.active.filter(postu_id=int(self.data.get('postu'))).order_by('name')
			except (ValueError, TypeError):
				pass
		elif self.instance.pk and self.instance.postu_id:
			self.fields['suku'].queryset = self.instance.postu.suku_set.order_by('name')

		if 'suku' in self.data:
			try:
				self.fields['aldeia'].queryset = Aldeia.active.filter(suku_id=int(self.data.get('suku'))).order_by('name')
			except (ValueError, TypeError):
				pass
		elif self.instance.pk and self.instance.suku_id:
			self.fields['aldeia'].queryset = self.instance.suku.aldeia_set.order_by('name')

		# Formuláriu fahe ba parte rua: seksaun 1–2 (helper) · formset seksaun 3 iha template · seksaun 4 no 6 (helper_b)
		self.helper = FormHelper()
		self.helper.form_tag = False          # <form> iha template (pola form.html)
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			section(1, 'Identifikasaun no Fatin'),
			Row(
				Column('titulu', css_class='form-group col-md-8 mb-0'),
				Column('data_relatoriu', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('munisipiu', css_class='form-group col-md-3 mb-0'),
				Column('postu', css_class='form-group col-md-3 mb-0'),
				Column('suku', css_class='form-group col-md-3 mb-0'),
				Column('aldeia', css_class='form-group col-md-3 mb-0'),
				css_class='form-row'
			),
			HTML(""" {% load i18n %}<div class="gps-box mb-2"><div class="d-flex justify-content-between align-items-center flex-wrap"><b><i class="fa fa-map-marker"></i> {% trans "Koordenada GPS" %}</b><button type="button" class="btn btn-sm btn-outline-rbr" id="btn-gps"><i class="fa fa-crosshairs"></i> {% trans "Foti GPS" %}</button></div><small id="gps-msg" class="text-muted">{% trans "Tenke iha fatin akontesimentu. Akurasia tenke ≤ 50 m." %}</small></div> """),
			Row(
				Column('latitude', css_class='form-group col-6 col-md-4 mb-0'),
				Column('longitude', css_class='form-group col-6 col-md-4 mb-0'),
				Column('gps_akurasia', css_class='form-group col-12 col-md-4 mb-0'),
				css_class='form-row'
			),
			section(2, 'Informasaun Insidente'),
			Row(
				Column('data_akontesimentu', css_class='form-group col-md-4 mb-0'),
				Column('tipu_rai', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('tipu_konflitu', css_class='form-group col-md-6 mb-0'),
				Column('tipu_seluk', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			'deskrisaun',
		)
		self.helper_b = FormHelper()
		self.helper_b.form_tag = False
		self.helper_b.disable_csrf = True
		self.helper_b.layout = Layout(
			section(4, 'Estragu Patrimóniu'),
			Row(
				Column('estragu', css_class='form-group col-md-6 mb-0'),
				Column('estragu_seluk', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			section(6, 'Nesesidade Urjente no Konsentimentu'),
			Row(
				Column('nesesidade', css_class='form-group col-md-6 mb-0'),
				Column('observasaun', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			Field('konsentimentu', wrapper_class='konsentimentu-box'),
			Field('la_publika'),                    # komunidade husu atu kazu la mosu iha portal públiku
		)

	def clean_munisipiu(self):
		# Campo disabled: uza munisípiu knaar (labele manipula husi browser)
		return self.munisipiu_knaar or self.cleaned_data.get('munisipiu')

	def clean(self):
		cleaned = super().clean()
		hoje = timezone.localdate()
		dr, da = cleaned.get('data_relatoriu'), cleaned.get('data_akontesimentu')
		if dr and dr > hoje:
			self.add_error('data_relatoriu', _('Data relatóriu labele iha futuru.'))
		if dr and da and da > dr:
			self.add_error('data_akontesimentu', _('Data akontesimentu labele liu data relatóriu.'))

		tipu = cleaned.get('tipu_konflitu') or []
		if any(t.presiza_esplika for t in tipu) and not cleaned.get('tipu_seluk'):
			self.add_error('tipu_seluk', _('Favor esplika tipu konflitu "Seluk".'))

		# Lokalizasaun tenke tuir malu (postu iha munisípiu, suku iha postu, aldeia iha suku)
		mun, postu, suku, aldeia = cleaned.get('munisipiu'), cleaned.get('postu'), cleaned.get('suku'), cleaned.get('aldeia')
		if postu and mun and postu.munisipiu_id != mun.pk:
			self.add_error('postu', _('Postu la iha munisípiu ne\'e.'))
		if suku and postu and suku.postu_id != postu.pk:
			self.add_error('suku', _('Suku la iha postu ne\'e.'))
		if aldeia and suku and aldeia.suku_id != suku.pk:
			self.add_error('aldeia', _('Aldeia la iha suku ne\'e.'))

		# GPS: tenke iha territóriu Timor-Leste no akurasia ≤ 50 m
		lat, lon, akur = cleaned.get('latitude'), cleaned.get('longitude'), cleaned.get('gps_akurasia')
		if lat is not None and lon is not None:
			if not (TL_LAT[0] <= lat <= TL_LAT[1] and TL_LON[0] <= lon <= TL_LON[1]):
				self.add_error('latitude', _('Koordenada GPS la iha territóriu Timor-Leste.'))
			if akur is not None and akur > GPS_MAX_AKURASIA:
				self.add_error('gps_akurasia', _('Akurasia GPS %(m)s m. Tenke ≤ 50 m.') % {'m': akur})

		# Bainhira haruka: kampu importante obrigatóriu
		if self.submit:
			obrigatoriu = {'postu': _('Postu Administrativu'), 'suku': _('Suku'), 'data_akontesimentu': _('Data Akontesimentu'),
				'deskrisaun': _('Deskrisaun Insidente'), 'latitude': _('Latitude'), 'longitude': _('Longitude')}
			for campo in obrigatoriu:
				if not cleaned.get(campo) and campo not in self.errors:
					self.add_error(campo, _('Kampu ne\'e obrigatóriu atu haruka.'))
			if not tipu:
				self.add_error('tipu_konflitu', _('Hili tipu konflitu rai.'))
			if not cleaned.get('konsentimentu'):
				self.add_error('konsentimentu', _('Laiha konsentimentu = labele rai kazu.'))
		return cleaned


class _InlineBase(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.render_hidden_fields = True     # id formset tenke iha


class AfetaduForm(_InlineBase):
	class Meta:
		model = UmaKainAfetada
		fields = ['uma_kain', 'total_ema', 'mane', 'feto', 'labarik', 'katuas_ferik', 'defisiensia']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper.layout = Layout(
			Row(
				Column('uma_kain', css_class='form-group col-6 col-md-3 mb-0'),
				Column('total_ema', css_class='form-group col-6 col-md-3 mb-0'),
				Column('mane', css_class='form-group col-6 col-md-3 mb-0'),
				Column('feto', css_class='form-group col-6 col-md-3 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('labarik', css_class='form-group col-6 col-md-4 mb-0'),
				Column('katuas_ferik', css_class='form-group col-6 col-md-4 mb-0'),
				Column('defisiensia', css_class='form-group col-6 col-md-4 mb-0'),
				css_class='form-row'
			),
		)

	def clean(self):
		cleaned = super().clean()
		total, mane, feto = cleaned.get('total_ema'), cleaned.get('mane'), cleaned.get('feto')
		if total is not None and mane is not None and feto is not None and mane + feto != total:
			self.add_error('total_ema', _('Mane + Feto tenke hanesan Total Ema (%(n)s).') % {'n': mane + feto})
		return cleaned


class InsidenteForm(_InlineBase):
	class Meta:
		model = InsidenteEviksaun
		fields = ['tipu_eviksaun', 'loron_avizu', 'forsa_seguransa', 'estragu', 'deskrisaun']
		widgets = {'deskrisaun': forms.Textarea(attrs={'rows': 2})}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['tipu_eviksaun'].queryset = TipuEviksaun.active.all()
		self.helper.layout = Layout(
			Row(
				Column('tipu_eviksaun', css_class='form-group col-md-4 mb-0'),
				Column('loron_avizu', css_class='form-group col-md-4 mb-0'),
				Column('forsa_seguransa', css_class='form-group col-md-4 mb-0 pt-md-4'),
				css_class='form-row'
			),
			Row(
				Column('estragu', css_class='form-group col-md-6 mb-0'),
				Column('deskrisaun', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
		)


class AtorForm(_InlineBase):
	class Meta:
		model = AtorEnvolvidu
		fields = ['tipu_ator', 'naran', 'papel']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['tipu_ator'].queryset = TipuAtor.active.all()
		self.helper.layout = Layout(
			Row(
				Column('tipu_ator', css_class='form-group col-md-4 mb-0'),
				Column('naran', css_class='form-group col-md-4 mb-0'),
				Column('papel', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
		)


AfetaduFormSet = inlineformset_factory(Kazu, UmaKainAfetada, form=AfetaduForm, extra=1, max_num=5, can_delete=True)
InsidenteFormSet = inlineformset_factory(Kazu, InsidenteEviksaun, form=InsidenteForm, extra=1, max_num=10, can_delete=True)
AtorFormSet = inlineformset_factory(Kazu, AtorEnvolvidu, form=AtorForm, extra=2, max_num=20, can_delete=True)


# ══════════════ EVIDÉNSIA ══════════════
MAX_FOTO, MAX_VIDEO = 5, 1
LIMITE = {  # tipu: (extensaun permite, tamañu máximu MB)
	Evidensia.FOTO: (('jpg', 'jpeg', 'png', 'webp'), 15),
	Evidensia.VIDEO: (('mp4', 'webm', 'mov', '3gp'), 50),
	Evidensia.DOKUMENTU: (('pdf', 'jpg', 'jpeg', 'png'), 10),
	Evidensia.DEKLARASAUN: (('pdf', 'jpg', 'jpeg', 'png'), 10),
}


class EvidensiaForm(forms.ModelForm):
	class Meta:
		model = Evidensia
		fields = ['tipu', 'file', 'naran', 'deskrisaun']

	def __init__(self, *args, **kwargs):
		self.kazu = kwargs.pop('kazu')
		super(EvidensiaForm, self).__init__(*args, **kwargs)
		self.fields['file'].widget.attrs.update({'accept': 'image/*,video/*,application/pdf', 'capture': 'environment'})
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('tipu', css_class='form-group col-md-4 mb-0'),
				Column('file', css_class='form-group col-md-8 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('naran', css_class='form-group col-md-6 mb-0'),
				Column('deskrisaun', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
		)

	def clean(self):
		cleaned = super().clean()
		tipu, f = cleaned.get('tipu'), cleaned.get('file')
		if not tipu or not f:
			return cleaned
		exts, max_mb = LIMITE[tipu]
		ext = f.name.lower().rsplit('.', 1)[-1] if '.' in f.name else ''
		if ext not in exts:
			self.add_error('file', _('Formatu file la permite. Uza: %(ext)s') % {'ext': ', '.join(exts)})
		if f.size > max_mb * 1024 * 1024:
			self.add_error('file', _('File boot liu. Máximu %(mb)s MB.') % {'mb': max_mb})
		if tipu == Evidensia.FOTO and self.kazu.foto_count() >= MAX_FOTO:
			self.add_error('tipu', _('Foto máximu 5 kada kazu.'))
		if tipu == Evidensia.VIDEO and self.kazu.video_count() >= MAX_VIDEO:
			self.add_error('tipu', _('Vídeo máximu 1 kada kazu.'))
		return cleaned


class ActionForm(forms.Form):
	nota = forms.CharField(label=_("Razaun / Nota"), required=False, widget=forms.Textarea(attrs={'rows': 2}))


class StatusKazuForm(forms.Form):
	status_kazu = forms.ChoiceField(label=_("Status Kazu"), choices=STATUS_KAZU_CHOICES)
	nota = forms.CharField(label=_("Nota"), required=False, max_length=255)
