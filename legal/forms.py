from django import forms
from django.utils import timezone
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


# ── Survei legál: "Perguntas Xave Sira Legal" (orden dokumentu, grupu subar to'o resposta) ──
from crispy_forms.layout import Div
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia
from kazu.forms import section, switch, grupu, seluk, _helper
from legal.models import SurveiLegal, SurveiLegalFile

GRUPU_MEIUS = {'ERANSA': 'eransa', 'SOSA': 'sosa', 'FOO': 'foo', 'POSSE': 'posse'}
SURVEI_GRUPU = {
	# grupu → kampu (server hamoos bainhira grupu subar)
	'eransa': ['eransa_husi_se', 'eransa_relasaun', 'eransa_herdeiru', 'eransa_rai_seluk', 'eransa_fahe',
		'eransa_fahe_ba_se', 'eransa_fahe_lokalizasaun', 'eransa_fahe_desde'],
	'eransa_fahe': ['eransa_fahe_ba_se', 'eransa_fahe_lokalizasaun', 'eransa_fahe_desde'],
	'sosa': ['sosa_husi_se', 'sosa_folin', 'sosa_bainhira', 'sosa_halo_saida', 'sosa_halo_desde', 'sosa_halo_se',
		'sosa_akordu', 'sosa_akordu_fatin', 'sosa_sasin', 'sasin_1', 'sasin_2', 'sasin_3', 'sasin_4'],
	'sosa_akordu': ['sosa_akordu_fatin'],
	'sosa_sasin': ['sasin_1', 'sasin_2', 'sasin_3', 'sasin_4'],
	'foo': ['foo_se', 'foo_bainhira', 'foo_akordu', 'foo_akordu_fatin', 'foo_relasaun'],
	'foo_akordu': ['foo_akordu_fatin'],
	'posse': ['posse_hahu', 'posse_halo_saida', 'posse_se_mak_halo', 'posse_periodu', 'posse_ema_seluk_tinan',
		'posse_relasaun_sosa', 'posse_uza_rai', 'posse_luan_rai', 'posse_luan_disputa', 'posse_luan_uma'],
	'entidade': ['entidade_naran', 'entidade_kontaktu', 'entidade_instituisaun', 'entidade_enderesu'],
	'estadu_seluk': ['parte_estadu_civil_seluk'],
}
SURVEI_KAMPU = ['kazu', 'titulu', 'data_survei', 'munisipiu', 'postu', 'suku', 'aldeia', 'latitude', 'longitude', 'gps_akurasia',
	'parte_naran', 'parte_sexu', 'parte_data_moris', 'parte_estadu_civil', 'parte_estadu_civil_seluk', 'parte_hela_fatin', 'parte_kartaun_eleitoral',
	'parte_profisaun', 'parte_kontaktu', 'parte_ehd'] + SURVEI_GRUPU['entidade'] + ['meius'] + SURVEI_GRUPU['eransa'] + \
	SURVEI_GRUPU['sosa'] + SURVEI_GRUPU['foo'] + SURVEI_GRUPU['posse'] + ['dok_identifikasaun', 'dok_relevante', 'fotografia', 'observasaun']
SURVEI_FATIN = ['munisipiu', 'postu', 'suku', 'aldeia', 'latitude', 'longitude', 'gps_akurasia']


def survei_grupu_ativu(d):
	# Regra hatudu/subar hanesan JS (online + offline): d = dict dadus
	meius = d.get('meius') or ''
	return {
		'entidade': any(d.get(c) for c in SURVEI_GRUPU['entidade']),
		'estadu_seluk': d.get('parte_estadu_civil') == 'SELUK',
		'eransa': meius == 'ERANSA', 'sosa': meius == 'SOSA', 'foo': meius == 'FOO', 'posse': meius == 'POSSE',
		'eransa_fahe': meius == 'ERANSA' and d.get('eransa_fahe') == 'SIN',
		'sosa_akordu': meius == 'SOSA' and d.get('sosa_akordu') == 'SIN',
		'sosa_sasin': meius == 'SOSA' and d.get('sosa_sasin') == 'SIN',
		'foo_akordu': meius == 'FOO' and d.get('foo_akordu') == 'SIN',
	}


def limpa_survei(d):
	# Kampu iha grupu subar → mamuk (la rai resposta ne'ebé la relevante)
	ativu = survei_grupu_ativu(d)
	for grp, kampu in SURVEI_GRUPU.items():
		if not ativu.get(grp):
			for c in kampu:
				if c in d:
					d[c] = None if c.startswith('parte_data') else ''
	return d


class SurveiLegalForm(forms.ModelForm):
	dok_identifikasaun = forms.MultipleChoiceField(label=_('Dokumentus identifikasaun'), required=False,
		choices=SurveiLegal.DOK_IDENTIFIKASAUN, widget=forms.CheckboxSelectMultiple)
	dok_relevante = forms.MultipleChoiceField(label=_('Dokumentus relevante sira seluk'), required=False,
		choices=SurveiLegal.DOK_RELEVANTE, widget=forms.CheckboxSelectMultiple)
	fotografia = forms.MultipleChoiceField(label=_('Fotografia'), required=False,
		choices=SurveiLegal.FOTOGRAFIA, widget=forms.CheckboxSelectMultiple)

	class Meta:
		model = SurveiLegal
		fields = SURVEI_KAMPU
		widgets = {
			'data_survei': DateInput(), 'parte_data_moris': DateInput(),
			'latitude': forms.TextInput(attrs={'readonly': True}), 'longitude': forms.TextInput(attrs={'readonly': True}),
			'gps_akurasia': forms.TextInput(attrs={'readonly': True}),
			'observasaun': forms.Textarea(attrs={'rows': 3}),
			**{c: forms.Textarea(attrs={'rows': 2}) for c in ['eransa_relasaun', 'eransa_herdeiru', 'eransa_fahe_ba_se',
				'eransa_fahe_lokalizasaun', 'sosa_halo_saida', 'foo_relasaun', 'posse_halo_saida', 'posse_relasaun_sosa', 'posse_uza_rai']},
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['kazu'].queryset = Kazu.objects.filter(status__in=KAZU_STATUS_LEGAL).order_by('-created_at')
		self.fields['kazu'].label = _('Kazu SIBAR (karik iha ona)')
		self.fields['kazu'].empty_label = _('— Kazu legál foun (fatin rasik) —')
		self.fields['kazu'].help_text = _("Hili kazu ne'ebé iha ona: fatin kopia husi kazu. Mamuk: prense fatin kazu legál foun.")
		self.fields['munisipiu'].required = False
		self.fields['munisipiu'].queryset = Munisipiu.active.all()
		# Dropdown bertingkat (hanesan formuláriu kazu)
		self.fields['postu'].queryset = PostuAdministrativu.objects.none()
		self.fields['suku'].queryset = Suku.objects.none()
		self.fields['aldeia'].queryset = Aldeia.objects.none()
		def _id(c):
			if c in self.data:
				try:
					return int(self.data.get(c))
				except (ValueError, TypeError):
					return None
			return getattr(self.instance, f'{c}_id', None)
		if _id('munisipiu'):
			self.fields['postu'].queryset = PostuAdministrativu.active.filter(munisipiu_id=_id('munisipiu')).order_by('name')
		if _id('postu'):
			self.fields['suku'].queryset = Suku.active.filter(postu_id=_id('postu')).order_by('name')
		if _id('suku'):
			self.fields['aldeia'].queryset = Aldeia.active.filter(suku_id=_id('suku')).order_by('name')

		col = lambda c, w: Column(c, css_class=f'form-group col-md-{w} mb-0')
		row = lambda *c: Row(*c, css_class='form-row')
		gps = HTML(""" {% load i18n %}<div class="mb-3"><button type="button" class="btn btn-outline-rbr btn-sm" id="btn-gps"><i class="fa fa-crosshairs"></i> {% trans "Foti GPS" %}</button> <small id="gps-msg" class="ml-2 text-muted"></small></div> """)
		self.helper_kazu = _helper(
			section(0, 'Kazu no Fatin'),
			row(col('kazu', 8), col('data_survei', 4)),
			Div(
				row(col('titulu', 12)),
				row(col('munisipiu', 3), col('postu', 3), col('suku', 3), col('aldeia', 3)),
				row(col('latitude', 4), col('longitude', 4), col('gps_akurasia', 4)), gps,
				css_class='kond sub-box', data_grp='fatin'),
		)
		self.helper_parte = _helper(
			section('I', 'Identifikasaun Parte Sira (Disputante Sira)'),
			row(col('parte_naran', 8), col('parte_sexu', 4)),
			row(col('parte_data_moris', 4), Column('parte_estadu_civil', seluk('parte_estadu_civil', 'parte_estadu_civil_seluk'),
				css_class='form-group col-md-4 mb-0'), col('parte_ehd', 4)),
			row(col('parte_hela_fatin', 12)),
			row(col('parte_kartaun_eleitoral', 4), col('parte_profisaun', 4), col('parte_kontaktu', 4)),
		)
		self.helper_entidade = _helper(
			section('II', "Entidade ne'ebe atu foti rai"),
			switch('entidade', "Iha entidade ne'ebé atu foti rai?"),
			grupu('entidade',
				row(col('entidade_naran', 8), col('entidade_kontaktu', 4)),
				row(col('entidade_instituisaun', 4), col('entidade_enderesu', 8))),
		)
		self.helper_meius = _helper(
			section('III', 'Perguntas Xave Sira'),
			row(col('meius', 6)),
			grupu('eransa', HTML(""" {% load i18n %}<h4 class="form-sub">1. {% trans "Eransa / Antesessor mate ona" %}</h4> """),
				'eransa_husi_se', 'eransa_relasaun', 'eransa_herdeiru',
				row(col('eransa_rai_seluk', 8), col('eransa_fahe', 4)),
				grupu('eransa_fahe', 'eransa_fahe_ba_se', 'eransa_fahe_lokalizasaun', 'eransa_fahe_desde')),
			grupu('sosa', HTML(""" {% load i18n %}<h4 class="form-sub">2. {% trans "Sosa" %}</h4> """),
				row(col('sosa_husi_se', 6), col('sosa_folin', 3), col('sosa_bainhira', 3)),
				'sosa_halo_saida',
				row(col('sosa_halo_desde', 6), col('sosa_halo_se', 6)),
				row(col('sosa_akordu', 4)),
				grupu('sosa_akordu', 'sosa_akordu_fatin'),
				row(col('sosa_sasin', 4)),
				grupu('sosa_sasin', HTML(""" {% load i18n %}<p class="small text-muted mb-1">{% trans "Semak sasin?" %}</p> """),
					row(col('sasin_1', 6), col('sasin_2', 6)), row(col('sasin_3', 6), col('sasin_4', 6)))),
			grupu('foo', HTML(""" {% load i18n %}<h4 class="form-sub">3. {% trans "Foó / doasaun (bele família ka ema seluk)" %}</h4> """),
				row(col('foo_se', 8), col('foo_bainhira', 4)),
				row(col('foo_akordu', 4)),
				grupu('foo_akordu', 'foo_akordu_fatin'),
				'foo_relasaun'),
			grupu('posse', HTML(""" {% load i18n %}<h4 class="form-sub">4. {% trans "Posse / okupa" %}</h4> """),
				row(col('posse_hahu', 6), col('posse_periodu', 6)),
				'posse_halo_saida',
				row(col('posse_se_mak_halo', 6), col('posse_ema_seluk_tinan', 6)),
				'posse_relasaun_sosa', 'posse_uza_rai',
				row(col('posse_luan_rai', 4), col('posse_luan_disputa', 4), col('posse_luan_uma', 4))),
		)
		self.helper_nota = _helper(
			section('IV', 'Notas importante nebeé tenki halo kompleta'),
			row(col('dok_identifikasaun', 4), col('dok_relevante', 8)),
			Div('fotografia', css_class='check-grid'),
			'observasaun',
		)

	def clean(self):
		d = super().clean()
		kazu = d.get('kazu')
		if kazu:
			# Kazu SIBAR: fatin husi kazu (la prense fali)
			for c in SURVEI_FATIN:
				d[c] = getattr(kazu, c)
			d['titulu'] = d.get('titulu') or (kazu.titulu or '')[:200]
		elif not d.get('munisipiu'):
			self.add_error('munisipiu', _('Munisípiu obrigatóriu ba kazu legál foun.'))
		dados = limpa_survei(dict(d))
		for c in SURVEI_KAMPU:
			if c in d and c in dados:
				d[c] = dados[c]
		return d


class SurveiFileForm(forms.ModelForm):
	class Meta:
		model = SurveiLegalFile
		fields = ['tipu', 'file', 'naran']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['file'].widget.attrs.update({'accept': ACCEPT})
		self.fields['naran'].required = False
		self.fields['tipu'].widget.attrs['class'] = 'custom-select custom-select-sm'


class AutorizasaunLegalForm(forms.Form):
	# Admin / Superadmin hili Ofisiál Legál (ida ka barak) + data hahú–remata
	users = forms.ModelMultipleChoiceField(label=_('Ofisiál Legál ne\'ebé bele input'), queryset=None, widget=forms.CheckboxSelectMultiple)
	data_hahu = forms.DateField(label=_('Data hahú'), required=False, widget=DateInput())
	data_remata = forms.DateField(label=_('Data remata'), required=False, widget=DateInput(), help_text=_('Mamuk = loron 7'))
	note = forms.CharField(label=_('Nota'), required=False, max_length=255)

	def __init__(self, *args, **kwargs):
		from django.contrib.auth.models import User
		from config.rbac import OFISIAL_LEGAL
		super().__init__(*args, **kwargs)
		self.fields['users'].queryset = User.objects.filter(groups__name=OFISIAL_LEGAL, is_active=True).select_related('pesoaluser__pesoal__munisipiu').distinct().order_by('username')
		self.fields['data_hahu'].initial = timezone.localdate()
		def _naran(u):
			p = getattr(getattr(u, 'pesoaluser', None), 'pesoal', None)
			mun = f' · {p.munisipiu}' if p and getattr(p, 'munisipiu', None) else ''
			return f'{p or u.username} ({u.email or u.username}){mun}'
		self.fields['users'].label_from_instance = _naran

	def clean(self):
		d = super().clean()
		hahu, remata = d.get('data_hahu'), d.get('data_remata')
		if remata and remata < (hahu or timezone.localdate()):
			self.add_error('data_remata', _('Data remata tenke depois data hahú.'))
		return d
