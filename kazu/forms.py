from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from config.file_check import valida_upload
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Field, Div
from custom.data.opsaun import TIPU_ENTIDADE
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia, TipuKonflitu, TipuRai, \
	TipuEviksaun, TipuAtor, EstraguPatrimoniu, NesesidadeUrjente
from kazu.models import Kazu, UmaKainAfetada, InsidenteEviksaun, AtorEnvolvidu, Evidensia, KazuSegimentu, KazuAkompanamentu, STATUS_KAZU_CHOICES

# Limite territóriu Timor-Leste (inklui Oé-Cusse no Ataúro)
TL_LAT = (Decimal('-9.60'), Decimal('-8.10'))
TL_LON = (Decimal('124.00'), Decimal('127.40'))
GPS_MAX_AKURASIA = 50


class DateInput(forms.DateInput):
	input_type = 'date'


# Títulu seksaun formuláriu (lista ne'e atu tools/extract_lian.py hetan testu ba tradusaun)
SECTION_TITLES = [_('Identifikasaun Kazu'), _('Fatin'), _('Populasaun Afetada'), _('Fokal Point no Organizasaun Seluk'),
	_('Tribunál no Notifikasaun'), _('Eviksaun no Status Kazu'), _('Informasaun Adisionál'), _('Konsentimentu'),
	_('Identifikasaun no Fatin'), _('Informasaun Insidente'), _('Atór Envolvidu no Populasaun Afetada'),
	_('Estragu Patrimóniu'), _('Evidénsia'), _('Nesesidade Urjente no Konsentimentu'),
	_('Status no Desizaun RbR'), _('Tribunál'), _('Notifikasaun'), _('Fokal Point RbR'), _("Organizasaun Seluk ne'ebé Akompaña")]
BTN_RAI = """ <button class="btn btn-rbr" type="submit"><i class="fa fa-save"></i> {% load i18n %}{% trans "Rai" %}</button> """


def section(num, title):
	return HTML(f""" {{% load i18n %}}<h3 class="form-section"><span>{num}</span> {{% trans "{title}" %}}</h3> """)


# Formuláriu badak: grupu opsionál subar to'o resposta (haree kazu/form.html no app offline)
SWITCH_LABELS = [_("Iha organizasaun seluk ne'ebé akompaña?"), _('Iha informasaun status kazu / desizaun RbR?'), _('Iha detalla rai (enderesu, luan)?'), _('Iha portavós komunidade?'), _('Iha atór envolvidu?'),
	_('Iha estragu patrimóniu?'), _('Iha nesesidade urjente?')]


def switch(grp, label):
	# Switch "Iha …?" → hatudu grupu data-grp=grp; JS loke automátiku se grupu iha ona dadus
	return HTML(f""" {{% load i18n %}}<div class="custom-control custom-switch mb-2"><input type="checkbox" class="custom-control-input" id="sw-{grp}" data-switch="{grp}"><label class="custom-control-label" for="sw-{grp}">{{% trans "{label}" %}}</label></div> """)


def grupu(grp, *fields):
	return Div(*fields, css_class='kond sub-box', data_grp=grp)


def seluk(kampu, *fields, ids=None):
	# Opsaun "Seluk" hili → hatudu kampu esplika (main.js: data-seluk-for). ids = valor checkbox "Seluk" (lista)
	attrs = {'data_seluk_for': kampu}
	if ids is not None:
		attrs['data_seluk_ids'] = ids
	return Div(*fields, css_class='seluk-box', **attrs)


# Pergunta formuláriu tuir orden dokumentu "Perguntas husi Baze de Dadus Central nian" (RbR)
LABEL_DOCX = {
	'titulu': _('Kazu'), 'data_relatoriu': _('Data Simu Kazu iha RbR'), 'tinan_simu': _('Tinan Simu Kazu iha RbR'),
	'tinan_disputa_hahu': _('Tinan Kazu Hahu'), 'tipu_konflitu': _('Tipu Kazu'), 'deskrisaun': _('Observasaun kona-ba tipu kazu'),
	'projetu': _("Projetu (karik kazu ne'e tipu Governu foti rai - foti atu hari'i saida?)"),
	'entidade_foti': _("Entidade ne'ebe foti rai (se mak foti rai?)"), 'entidade_kategoria': _('Entidade Benefisiariu (kategoria)'),
	'munisipiu': _('Munisipiu'), 'postu': _('Postu Administrativu'), 'suku': _('Suku'), 'aldeia': _('Aldeia'),
	'enderesu_fatin': _('Enderesu ka Deskrisaun Fatin'), 'rai_luan': _('Rai nia Luan (Metru ka Hektar)'),
	'iha_dadus_uma_kain': _('Dadus Uma Kain iha ka lae?'), 'fonte_dadus_uma_kain': _('Fontes Dadus Uma Kain'),
	'observasaun_afetadu': _('Observasaun kona-ba dadus ema afetadu'),
	'portavos_observasaun': _('Observasaun ruma kona ba portavos'), 'portavos_naran': _('Naran portavos husi komunidade'),
	'portavos_kontaktu': _('Numero kontaktu portavos komunidade'),
	'eviksaun_akontese': _('Eviksaun Akontese ona?'), 'data_eviksaun': _('Data Eviksaun'),
	'observasaun_eviksaun': _('Observasaun kona-ba eviksaun rasik'),
	'konsultasaun_molok': _('Molok eviksaun iha konsultasaun ka lae?'), 'notifikasaun_klaru': _('Molok eviksaun iha notifikasaun klaru ka lae?'),
	'uza_forsa': _('Durante eviksaun uza forsa ka lae?'),
}


class KazuForm(forms.ModelForm):
	numeru_rbr = forms.IntegerField(label=_('Numeru kazu'), required=False, min_value=1,
		help_text=_("Bele hetan numero husi versaun hard copy (file). Hakerek numero deit, lalika hakerek 'RBR'"))
	data_relatoriu = forms.DateField(label=_("Data Simu Kazu iha RbR"), widget=DateInput(), required=False, initial=timezone.localdate)
	data_akontesimentu = forms.DateField(label=_("Data Akontesimentu"), widget=DateInput(), required=False)
	data_eviksaun = forms.DateField(label=_("Data Eviksaun"), widget=DateInput(), required=False)
	akompanamentu_foun = forms.CharField(label=_('Akompanamentu ba Kazu'), required=False,
		widget=forms.Textarea(attrs={'rows': 2, 'placeholder': _("Saida mak RbR halo? (vizita, reuniaun, karta, mediasaun…)")}))

	class Meta:
		model = Kazu
		# Kampu tabela Kazu; kampu seksaun (fatin, entidade, populasaun, eviksaun, portavós) aumenta iha okos (KAMPU_SEKSAUN_FORM)
		fields = ['titulu', 'data_relatoriu', 'tinan_simu', 'munisipiu', 'postu', 'suku', 'aldeia',
			'latitude', 'longitude', 'gps_akurasia', 'data_akontesimentu', 'tinan_disputa_hahu', 'tipu_konflitu', 'tipu_seluk', 'tipu_rai',
			'deskrisaun', 'estragu', 'estragu_seluk', 'nesesidade', 'konsentimentu', 'la_publika', 'observasaun']
		labels = LABEL_DOCX
		help_texts = {'titulu': _("Naran kazu ne'ebe Sekretariadu rejistu"), 'tinan_disputa_hahu': _("Tinan ne'ebe disputa hahu entre parte rua"),
			'tinan_simu': _('Automátiku husi Data Simu. Hakerek tinan de\'it se data la hatene.')}
		widgets = {
			'tipu_konflitu': forms.CheckboxSelectMultiple,
			'estragu': forms.CheckboxSelectMultiple,
			'nesesidade': forms.CheckboxSelectMultiple,
			'deskrisaun': forms.Textarea(attrs={'rows': 4, 'placeholder': _('Fo esplikasaun badak kona ba tipu kazu, se karik presiza.')}),
			'observasaun': forms.Textarea(attrs={'rows': 2}),
			'tinan_disputa_hahu': forms.NumberInput(attrs={'min': 1900, 'placeholder': _('ex. 2019')}),
			'tinan_simu': forms.NumberInput(attrs={'min': 1900, 'placeholder': _('ex. 2019')}),
			'latitude': forms.NumberInput(attrs={'readonly': True, 'step': 'any'}),
			'longitude': forms.NumberInput(attrs={'readonly': True, 'step': 'any'}),
			'gps_akurasia': forms.NumberInput(attrs={'readonly': True}),
		}

	def __init__(self, *args, **kwargs):
		knaar = kwargs.pop('munisipiu_knaar', None)
		# Munisípiu knaar Investigadór: ida (fixu) ka rua (hili) — Admin / Superadmin mak determina
		self.knaar_lista = [m for m in (knaar if isinstance(knaar, (list, tuple)) else [knaar]) if m]
		self.submit = kwargs.pop('submit', False)
		super(KazuForm, self).__init__(*args, **kwargs)
		if self.instance.pk:                           # valór kampu seksaun (tabela OneToOne)
			for c in KAMPU_SEKSAUN_FORM:
				if c not in self.initial:
					self.initial[c] = getattr(self.instance, c)
		self.fields['tipu_konflitu'].queryset = TipuKonflitu.active.all()
		self.fields['tipu_rai'].queryset = TipuRai.active.all()
		self.fields['estragu'].queryset = EstraguPatrimoniu.active.all()
		self.fields['nesesidade'].queryset = NesesidadeUrjente.active.all()
		self.estragu_seluk_ids = ','.join(str(pk) for pk in EstraguPatrimoniu.objects.filter(code='SELUK').values_list('pk', flat=True))
		ref = (self.instance.referensia_rbr or '') if self.instance.pk else ''
		if ref.upper().startswith('RBR/') and ref[4:].isdigit():
			self.fields['numeru_rbr'].initial = int(ref[4:])
		# Iha poligon → Rai nia luan kalkula husi poligon (la bele hakerek)
		if self.instance.pk and self.instance.poligon:
			for c in ('rai_luan', 'rai_luan_unidade'):
				self.fields[c].disabled = True
			self.fields['rai_luan'].help_text = _('Kalkula automátiku husi poligon rai (edita poligon iha detalla kazu).')
		# Tipu Governu / entidade legál → hatudu Projetu no Entidade (JS lee lista id)
		self.fields['tipu_konflitu'].widget.attrs['data-entidade-ids'] = ','.join(
			str(pk) for pk in TipuKonflitu.objects.filter(code__in=TIPU_ENTIDADE).values_list('pk', flat=True))
		self.fields['tipu_konflitu'].widget.attrs['data-seluk-ids'] = ','.join(
			str(pk) for pk in TipuKonflitu.objects.filter(presiza_esplika=True).values_list('pk', flat=True))

		# Investigadór: munisípiu knaar deit (ida → fixu; rua → hili)
		self.knaar_ids = [m.pk for m in self.knaar_lista]
		if self.knaar_ids and self.instance.pk and self.instance.munisipiu_id and self.instance.munisipiu_id not in self.knaar_ids:
			self.knaar_ids.append(self.instance.munisipiu_id)      # kazu tuan iha munisípiu uluk: la lakon
		self.munisipiu_knaar = Munisipiu.objects.get(pk=self.knaar_ids[0]) if len(self.knaar_ids) == 1 else None
		if self.munisipiu_knaar:
			self.fields['munisipiu'].queryset = Munisipiu.objects.filter(pk=self.munisipiu_knaar.pk)
			self.fields['munisipiu'].initial = self.munisipiu_knaar.pk
			self.fields['munisipiu'].disabled = True
		elif self.knaar_ids:
			self.fields['munisipiu'].queryset = Munisipiu.objects.filter(pk__in=self.knaar_ids)
			self.fields['munisipiu'].required = True
			self.fields['munisipiu'].empty_label = _('— Hili munisípiu —')
			self.fields['munisipiu'].help_text = _('Ita iha munisípiu knaar rua: hili ida ba kazu ne\'e.')
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
		if self.knaar_ids and munisipiu_id not in self.knaar_ids:
			munisipiu_id = None                          # la'ós munisípiu knaar
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

		# Formuláriu tuir orden dokumentu (pergunta 1–65); template hatudu helper sira ho formset no segimentu
		col = lambda c, w: Column(c, css_class=f'form-group col-md-{w} mb-0')
		self.helper_a = _helper(        # 1. Identifikasaun kazu (pergunta 1–10)
			section(1, 'Identifikasaun Kazu'),
			Row(col('numeru_rbr', 3), col('data_relatoriu', 3), col('tinan_simu', 3), col('tinan_disputa_hahu', 3), css_class='form-row'),
			'titulu',
			Row(col('tipu_konflitu', 6), Column(grupu('seluk', 'tipu_seluk'), css_class='col-md-6'), css_class='form-row'),   # "Seluk" → esplika
			'deskrisaun',
			grupu('entidade', 'projetu'),           # tipu Governu / entidade legál
		)
		# Troka "Iha atór envolvidu?": entidade ne'ebé foti rai + kategoria (Seluk → esplika)
		self.helper_entidade = _helper(
			switch('entidade_foti', "Entidade ne'ebe foti rai (se mak foti rai?)"),
			grupu('entidade_foti',
				Row(col('entidade_foti', 6), col('entidade_kategoria', 6), css_class='form-row'),
				seluk('entidade_kategoria', 'entidade_kategoria_seluk')),
		)
		self.helper_b = _helper(        # 2. Fatin (pergunta 11–17)
			section(2, 'Fatin'),
			Row(col('munisipiu', 3), col('postu', 3), col('suku', 3), col('aldeia', 3), css_class='form-row'),
			HTML(""" {% load i18n %}<div class="gps-box mb-2"><div class="d-flex justify-content-between align-items-center flex-wrap"><b><i class="fa fa-map-marker"></i> {% trans "Pontu Kordenadu (GPS)" %}</b><button type="button" class="btn btn-sm btn-outline-rbr" id="btn-gps"><i class="fa fa-crosshairs"></i> {% trans "Foti GPS" %}</button></div><small id="gps-msg" class="text-muted">{% trans "Tenke iha fatin akontesimentu. Akurasia tenke ≤ 50 m." %}</small></div> """),
			Row(Column('latitude', css_class='form-group col-6 col-md-4 mb-0'), Column('longitude', css_class='form-group col-6 col-md-4 mb-0'),
				Column('gps_akurasia', css_class='form-group col-12 col-md-4 mb-0'), css_class='form-row'),
			switch('rai', 'Iha detalla rai (enderesu, luan)?'),
			grupu('rai', 'enderesu_fatin',
				Row(Column('rai_luan', css_class='form-group col-7 col-md-4 mb-0'), Column('rai_luan_unidade', css_class='form-group col-5 col-md-3 mb-0'), css_class='form-row')),
		)
		self.helper_pop = _helper(      # 3. Populasaun afetada (pergunta 18; formset 19–25 iha template)
			section(3, 'Populasaun Afetada'),
			Row(col('iha_dadus_uma_kain', 4), css_class='form-row'),
		)
		self.helper_pop_b = _helper(grupu('uma_kain', 'fonte_dadus_uma_kain', 'observasaun_afetadu'))   # 26–27
		self.helper_portavos = _helper(  # 38–39 / 64–65: portavós komunidade
			switch('portavos', 'Iha portavós komunidade?'),
			grupu('portavos', 'portavos_observasaun', Row(col('portavos_naran', 7), col('portavos_kontaktu', 5), css_class='form-row')),
		)
		self.helper_eviksaun = _helper(  # 6. Eviksaun (pergunta 51–53)
			section(6, 'Eviksaun no Status Kazu'),
			Row(col('eviksaun_akontese', 4), css_class='form-row'),
			grupu('eviksaun', Row(col('data_eviksaun', 4), css_class='form-row'), 'observasaun_eviksaun'),
		)
		self.helper_eviksaun_b = _helper(  # 59–61 (depois status kazu, tuir dokumentu)
			grupu('eviksaun', Row(col('konsultasaun_molok', 4), col('notifikasaun_klaru', 4), col('uza_forsa', 4), css_class='form-row')),
		)
		self.helper_akomp = _helper('akompanamentu_foun')   # 63
		self.helper_extra = _helper(     # 7. Informasaun adisionál SIBAR (la iha iha dokumentu)
			section(7, 'Informasaun Adisionál'),
			Row(col('data_akontesimentu', 4), col('tipu_rai', 4), css_class='form-row'),
		)
		self.helper_b2 = _helper(
			switch('estragu', 'Iha estragu patrimóniu?'),
			grupu('estragu', Row(col('estragu', 6), Column(seluk('estragu', 'estragu_seluk', ids=self.estragu_seluk_ids), css_class='col-md-6'), css_class='form-row')),
			switch('nesesidade', 'Iha nesesidade urjente?'),
			grupu('nesesidade', 'nesesidade'),
			'observasaun',
			section(8, 'Konsentimentu'),
			Field('konsentimentu', wrapper_class='konsentimentu-box'),
			Field('la_publika'),                    # komunidade husu atu kazu la mosu iha portal públiku
		)

	def clean_munisipiu(self):
		# Campo disabled: uza munisípiu knaar (labele manipula husi browser)
		return self.munisipiu_knaar or self.cleaned_data.get('munisipiu')     # rua: queryset limita ba knaar

	def clean_numeru_rbr(self):
		n = self.cleaned_data.get('numeru_rbr')
		if n and Kazu.objects.filter(referensia_rbr__iexact=f'RBR/{n}').exclude(pk=self.instance.pk).exists():
			raise forms.ValidationError(_("Numeru kazu RBR/%(n)s iha sistema ona.") % {'n': n})
		return n

	def clean(self):
		cleaned = super().clean()
		hoje = timezone.localdate()
		dr, da = cleaned.get('data_relatoriu'), cleaned.get('data_akontesimentu')
		if dr and dr > hoje:
			self.add_error('data_relatoriu', _('Data relatóriu labele iha futuru.'))
		if dr and da and da > dr:
			self.add_error('data_akontesimentu', _('Data akontesimentu labele liu data relatóriu.'))
		if dr:
			cleaned['tinan_simu'] = dr.year             # Tinan Simu automátiku husi data
		for campo in ('tinan_disputa_hahu', 'tinan_simu'):
			tinan = cleaned.get(campo)
			if tinan and not (1900 <= tinan <= hoje.year):
				self.add_error(campo, _('Tinan la validu (1900 to\'o %(t)s).') % {'t': hoje.year})
		if not dr and not cleaned.get('tinan_simu'):
			self.add_error('data_relatoriu', _('Hakerek Data Simu ka Tinan Simu Kazu iha RbR.'))
		de = cleaned.get('data_eviksaun')
		if de and de > hoje:
			self.add_error('data_eviksaun', _('Data eviksaun labele iha futuru.'))
		if cleaned.get('rai_luan') is not None and cleaned['rai_luan'] < 0:
			self.add_error('rai_luan', _('Rai nia luan tenke pozitivu.'))

		tipu = cleaned.get('tipu_konflitu') or []
		if any(t.presiza_esplika for t in tipu) and not cleaned.get('tipu_seluk'):
			self.add_error('tipu_seluk', _('Favor esplika tipu konflitu "Seluk".'))

		# Resposta kondisionál: kampu ne'ebé la aplika la rai (hanesan formuláriu subar)
		if tipu and not any(t.presiza_esplika for t in tipu):
			cleaned['tipu_seluk'] = ''
		if tipu and not any(t.code in TIPU_ENTIDADE for t in tipu):
			cleaned['projetu'] = ''
		if cleaned.get('entidade_kategoria') != 'SELUK':
			cleaned['entidade_kategoria_seluk'] = ''
		if cleaned.get('eviksaun_akontese') != 'SIN':
			cleaned.update(data_eviksaun=None, konsultasaun_molok='', notifikasaun_klaru='', uza_forsa='', observasaun_eviksaun='')
		if cleaned.get('iha_dadus_uma_kain') in ('LAE', 'LAHATENE'):
			cleaned.update(fonte_dadus_uma_kain='', observasaun_afetadu='')

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
			obrigatoriu = {'postu': _('Postu Administrativu'), 'suku': _('Suku'), 'latitude': _('Latitude'), 'longitude': _('Longitude')}
			for campo in obrigatoriu:
				if not cleaned.get(campo) and campo not in self.errors:
					self.add_error(campo, _('Kampu ne\'e obrigatóriu atu haruka.'))
			if not tipu:
				self.add_error('tipu_konflitu', _('Hili tipu konflitu rai.'))
			if not cleaned.get('konsentimentu'):
				self.add_error('konsentimentu', _('Laiha konsentimentu = labele rai kazu.'))
		return cleaned

	def save(self, commit=True):
		obj = super().save(commit=False)
		for c in KAMPU_SEKSAUN_FORM:                   # Kazu.save() rai seksaun sira
			if c in self.cleaned_data:
				setattr(obj, c, self.cleaned_data[c])
		n = self.cleaned_data.get('numeru_rbr')
		if n:
			obj.referensia_rbr = f'RBR/{n}'
		elif 'numeru_rbr' in self.changed_data and (obj.referensia_rbr or '').upper().startswith('RBR/'):
			obj.referensia_rbr = None                   # numeru hamoos
		if commit:
			obj.save()
			self.save_m2m()
		return obj



# Kampu husi tabela seksaun (naran hanesan uluk: formuláriu, app offline no sinkron la muda)
KAMPU_SEKSAUN_FORM = [c for c in Kazu.KAMPU_SEKSAUN if c not in ('poligon', 'poligon_luan_m2', 'poligon_keliling_m')]
KazuForm.base_fields.update({c: f for c, f in forms.fields_for_model(
	Kazu.SEKSAUN['fatin'], fields=['enderesu_fatin', 'rai_luan', 'rai_luan_unidade'], labels=LABEL_DOCX).items()})
for _rel in ('entidade', 'populasaun', 'eviksaun', 'portavos'):
	KazuForm.base_fields.update(forms.fields_for_model(Kazu.SEKSAUN[_rel], exclude=['kazu', 'data_eviksaun'], labels=LABEL_DOCX,
		widgets={'observasaun_afetadu': forms.Textarea(attrs={'rows': 2}), 'observasaun_eviksaun': forms.Textarea(attrs={'rows': 2})}))


def _helper(*layout):
	h = FormHelper()
	h.form_tag = False
	h.disable_csrf = True
	h.layout = Layout(*layout)
	return h


# Segimentu iha formuláriu kazu (pergunta 33–37, 40–50, 54–58); Fokal point automátiku (la iha formuláriu)
LABEL_SEG_DOCX = {
	'org_seluk': _("Organizasaun seluk ne'ebé halo akompaniamentu"), 'org_seluk_naran': _('Naran ema husi organizasaun seluk'),
	'org_seluk_kontaktu': _('Numor Kontaktu (ema husi org seluk)'),
	'tribunal_rejistu': _('Rejistu iha tribunal?'), 'tribunal_data': _('Data rejistu iha tribunal'),
	'tribunal_representa': _('Se mak rejistu ka representa'), 'advogadu_kontaktu': _('Informasaun kontaktu advogadu nian'),
	'tribunal_observasaun': _('Observasaun kona-ba prosesu tribunal'), 'tribunal_desizaun': _('Iha ona desizaun husi tribunal'),
	'tribunal_desizaun_seluk': _('Esplika desizaun tribunal "Seluk"'),
	'tribunal_desizaun_data': _('Desizaun hatun sá data?'), 'notif_simu': _('Simu Notifikasaun Ona?'),
	'notif_data': _('Data simu notifikasaun'), 'notif_observasaun': _('Observasaun kona-ba prosesu notifikasaun'),
	'notif_husi': _('Notifikasaun husi se?'), 'data_ikus_cek': _('Data ikus cek status kazu'), 'status_rezolusaun': _('Status Kazu'),
	'desizaun_rbr': _("RBR nia desizaun ba Kazu ne'e"), 'observasaun_kazu': _('Observasaun kona ba kazu'),
}


class SegimentuKazuForm(forms.ModelForm):
	class Meta:
		model = KazuSegimentu
		fields = list(LABEL_SEG_DOCX)
		labels = LABEL_SEG_DOCX
		help_texts = {
			'advogadu_kontaktu': _('Advogadu nia naran sa, telefone, organizasaun'),
			'status_rezolusaun': _('Karik RbR refere kazu ida ne tiha ona, bele husik mamuk'),
			'desizaun_rbr': _("'Arkivu' signifika katak kazu resolve ona ka RbR refere ona ba advogadu privadu sira."),
			'observasaun_kazu': _('Fo esplikasaun badak kona ba RbR nia desizaun kona ba kazu ida ne'),
		}
		widgets = {
			'tribunal_data': DateInput(), 'tribunal_desizaun_data': DateInput(), 'notif_data': DateInput(), 'data_ikus_cek': DateInput(),
			'tribunal_observasaun': forms.Textarea(attrs={'rows': 2}), 'notif_observasaun': forms.Textarea(attrs={'rows': 2}),
			'observasaun_kazu': forms.Textarea(attrs={'rows': 2}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		col = lambda c, w: Column(c, css_class=f'form-group col-md-{w} mb-0')
		self.helper_org = _helper(       # 4. Fokal point (automátiku) + organizasaun seluk (pergunta 28–37)
			section(4, 'Fokal Point no Organizasaun Seluk'),
			HTML(""" {% load i18n %}<div class="alert alert-light border small py-2"><i class="fa fa-user"></i> {% trans "Fokal Point RbR (pergunta 28–32): automátiku husi Investigadór ne'ebé rejista kazu. Admin bele muda iha detalla kazu." %}</div> """),
			switch('org', "Iha organizasaun seluk ne'ebé akompaña?"),
			grupu('org', Row(col('org_seluk', 4), col('org_seluk_naran', 4), col('org_seluk_kontaktu', 4), css_class='form-row')),
		)
		self.helper_tribunal = _helper(  # 5. Tribunál no notifikasaun (pergunta 40–50)
			section(5, 'Tribunál no Notifikasaun'),
			Row(col('tribunal_rejistu', 4), css_class='form-row'),
			grupu('tribunal',                # Rejistu = Sin / Agora dadaun → detalla tribunál
				Row(col('tribunal_data', 4), col('tribunal_representa', 8), css_class='form-row'),
				'advogadu_kontaktu', 'tribunal_observasaun',
				Row(col('tribunal_desizaun', 6), Column(grupu('tribunal_desizaun', 'tribunal_desizaun_data'),
					seluk('tribunal_desizaun', 'tribunal_desizaun_seluk'), css_class='col-md-6'), css_class='form-row'),
			),
			Row(col('notif_simu', 4), css_class='form-row'),
			grupu('notif', Row(col('notif_data', 4), col('notif_husi', 8), css_class='form-row'), 'notif_observasaun'),   # Simu = Sin
		)
		self.helper_status = _helper(    # pergunta 54–58
			switch('status', 'Iha informasaun status kazu / desizaun RbR?'),
			grupu('status', Row(col('data_ikus_cek', 4), col('status_rezolusaun', 8), css_class='form-row'), 'desizaun_rbr', 'observasaun_kazu'),
		)

	def clean(self):
		# Resposta kondisionál: detalla ne'ebé la aplika la rai (hanesan formuláriu subar)
		cleaned = super().clean()
		if cleaned.get('tribunal_rejistu') not in ('SIN', 'DADAUN'):
			cleaned.update(tribunal_data=None, tribunal_representa='', advogadu_kontaktu='', tribunal_observasaun='',
				tribunal_desizaun='', tribunal_desizaun_data=None)
		if cleaned.get('tribunal_desizaun') != 'SIN':
			cleaned['tribunal_desizaun_data'] = None
		if cleaned.get('tribunal_desizaun') != 'SELUK':
			cleaned['tribunal_desizaun_seluk'] = ''
		if cleaned.get('notif_simu') != 'SIN':
			cleaned.update(notif_data=None, notif_observasaun='', notif_husi='')
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
				css_class='form-row'
			),
			grupu('uma_kain',
				Row(
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
MAX_FOTO, MAX_VIDEO = 5, 3
LIMITE = {  # tipu: (tipu konteúdu permite — verifika husi bytes, la'ós extensaun; tamañu máximu MB)
	Evidensia.FOTO: ({'jpg', 'png', 'webp'}, 15),
	Evidensia.VIDEO: ({'mp4', 'webm'}, 50),
	Evidensia.DOKUMENTU: ({'pdf', 'jpg', 'png'}, 10),
	Evidensia.DEKLARASAUN: ({'pdf', 'jpg', 'png'}, 10),
}


class MultiFileInput(forms.ClearableFileInput):
	allow_multiple_selected = True


class MultiFileField(forms.FileField):
	# Field file ida ne'ebé simu file barak (galeria) — retorna lista
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('widget', MultiFileInput())
		super().__init__(*args, **kwargs)

	def clean(self, data, initial=None):
		single = super().clean
		if isinstance(data, (list, tuple)):
			return [single(d, initial) for d in data] if data else [single(None, initial)]
		return [single(data, initial)]


class EvidensiaForm(forms.ModelForm):
	# Foto: kámera ka galeria (foto barak dala ida); vídeo / dokumentu: file ida
	file = MultiFileField(label=_("File"))

	class Meta:
		model = Evidensia
		fields = ['tipu', 'naran', 'deskrisaun']

	def __init__(self, *args, **kwargs):
		self.kazu = kwargs.pop('kazu')
		super(EvidensiaForm, self).__init__(*args, **kwargs)
		self.fields['file'].widget.attrs.update({'accept': 'image/*,video/*,application/pdf'})
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('tipu', css_class='form-group col-md-4 mb-0'),
				Column(
					HTML(""" {% load i18n %}<div class="evid-fonte mb-2">
						<button type="button" class="btn btn-rbr btn-sm" data-fonte="kamera"><i class="fa fa-camera"></i> {% trans "Foti Foto" %}</button>
						<button type="button" class="btn btn-outline-rbr btn-sm" data-fonte="galeria"><i class="fa fa-picture-o"></i> {% trans "Galeria" %}</button>
					</div> """),
					'file',
					HTML(""" <div id="evid-pratinjau" class="evid-pratinjau"></div> """),
					css_class='form-group col-md-8 mb-0'
				),
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
		tipu, files = cleaned.get('tipu'), cleaned.get('file') or []
		if not tipu or not files:
			return cleaned
		permite, max_mb = LIMITE[tipu]
		for f in files:
			try:
				valida_upload(f, permite, max_mb)          # konteúdu loos, la fiar extensaun
			except ValidationError as e:
				self.add_error('file', e)
		if tipu == Evidensia.FOTO:
			restu = MAX_FOTO - self.kazu.foto_count()
			if restu <= 0:
				self.add_error('tipu', _('Foto máximu 5 kada kazu.'))
			elif len(files) > restu:
				self.add_error('file', _('Foto máximu 5 kada kazu: ita bele aumenta %(n)s tan deit.') % {'n': restu})
		elif len(files) > 1:
			self.add_error('file', _('Vídeo ka dokumentu: file ida deit kada upload.'))
		if tipu == Evidensia.VIDEO and self.kazu.video_count() >= MAX_VIDEO:
			self.add_error('tipu', _('Vídeo máximu %(n)s kada kazu.') % {'n': MAX_VIDEO})
		return cleaned


class ActionForm(forms.Form):
	nota = forms.CharField(label=_("Razaun / Nota"), required=False, widget=forms.Textarea(attrs={'rows': 2}))


# ══════════════ Import Excel + hadia lokasaun (Admin) ══════════════
class ImportForm(forms.Form):
	file = forms.FileField(label=_("File Excel (.xlsx) ka CSV"), help_text=_("Template ka export baze dadus sentrál RbR (Airtable \"Kazu Hotu\"). Máximu 500 liña, 5 MB."))

	def __init__(self, *args, **kwargs):
		super(ImportForm, self).__init__(*args, **kwargs)
		self.fields['file'].widget.attrs.update({'accept': '.xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv'})
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			'file',
			HTML(""" <button class="btn btn-rbr" type="submit"><i class="fa fa-upload"></i> {% load i18n %}{% trans "Upload no haree pratinjau" %}</button> """)
		)

	def clean_file(self):
		f = self.cleaned_data.get('file')
		if f:
			valida_upload(f, {'xlsx', 'csv'}, 5)          # Excel loos (la ho makro) ka CSV testu
		return f


class LokasaunForm(forms.Form):
	# Koordenada husi marka iha mapa (bele hakerek mós)
	latitude = forms.DecimalField(label=_("Latitude"), max_digits=9, decimal_places=6)
	longitude = forms.DecimalField(label=_("Longitude"), max_digits=9, decimal_places=6)

	def __init__(self, *args, **kwargs):
		super(LokasaunForm, self).__init__(*args, **kwargs)
		for f in ('latitude', 'longitude'):
			self.fields[f].widget.attrs.update({'step': '0.000001', 'inputmode': 'decimal'})
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('latitude', css_class='form-group col-md-6 mb-0'),
				Column('longitude', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			HTML(""" <button class="btn btn-rbr" type="submit"><i class="fa fa-save"></i> {% load i18n %}{% trans "Rai lokasaun" %}</button> """)
		)

	def clean(self):
		cleaned = super().clean()
		lat, lon = cleaned.get('latitude'), cleaned.get('longitude')
		if lat is not None and lon is not None and not (TL_LAT[0] <= lat <= TL_LAT[1] and TL_LON[0] <= lon <= TL_LON[1]):
			raise forms.ValidationError(_('Koordenada GPS la iha territóriu Timor-Leste.'))
		return cleaned


# ══════════════ Segimentu kazu (eskritóriu RbR) ══════════════
# Segimentu fahe ba seksaun: kada seksaun iha butaun rasik (edita no rai seksaun ida de'it)
SEGIMENTU_SEKSAUN = [
	('status', _('Status no Desizaun RbR'), [[('data_ikus_cek', 3), ('status_rezolusaun', 5), ('desizaun_rbr', 4)], [('observasaun_kazu', 12)]]),
	('tribunal', _('Tribunál'), [[('tribunal_rejistu', 4), ('tribunal_data', 4), ('tribunal_representa', 4)],
		[('advogadu_kontaktu', 6), ('tribunal_desizaun', 3), ('tribunal_desizaun_data', 3)], [('tribunal_desizaun_seluk', 12)], [('tribunal_observasaun', 12)]]),
	('notifikasaun', _('Notifikasaun'), [[('notif_simu', 4), ('notif_data', 4), ('notif_husi', 4)], [('notif_observasaun', 12)]]),
	('fokal', _('Fokal Point RbR'), [[('fokal_naran', 4), ('fokal_telemovel', 4), ('fokal_tipu', 4)], [('fokal_organizasaun', 6), ('fokal_enderesu', 6)]]),
	('org_seluk', _("Organizasaun Seluk ne'ebé Akompaña"), [[('org_seluk', 4), ('org_seluk_naran', 4), ('org_seluk_kontaktu', 4)]]),
]
SEGIMENTU_KAMPU = {k: [c for row in rows for c, _w in row] for k, _t, rows in SEGIMENTU_SEKSAUN}


class SegimentuForm(forms.ModelForm):
	class Meta:
		model = KazuSegimentu
		exclude = ['kazu', 'updated_by']
		widgets = {
			'tribunal_data': DateInput(), 'tribunal_desizaun_data': DateInput(), 'notif_data': DateInput(), 'data_ikus_cek': DateInput(),
			'tribunal_observasaun': forms.Textarea(attrs={'rows': 2}), 'notif_observasaun': forms.Textarea(attrs={'rows': 2}),
			'observasaun_kazu': forms.Textarea(attrs={'rows': 3}),
		}

	def __init__(self, *args, seksaun=None, **kwargs):
		# seksaun: kampu husi seksaun ida de'it (seluk la muda bainhira rai)
		super(SegimentuForm, self).__init__(*args, **kwargs)
		seksaun = seksaun or SEGIMENTU_SEKSAUN[0][0]
		for c in list(self.fields):
			if c not in SEGIMENTU_KAMPU[seksaun]:
				del self.fields[c]
		if 'desizaun_rbr' in self.fields:
			self.fields['desizaun_rbr'].help_text = _("'Arkivu' = kazu resolve ona ka RbR refere ona ba advogadu privadu.")
		if 'status_rezolusaun' in self.fields:
			self.fields['status_rezolusaun'].help_text = _("Se RbR refere kazu ne'e ona, bele husik mamuk.")
		rows = dict((k, r) for k, _t, r in SEGIMENTU_SEKSAUN)[seksaun]
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		cel = lambda c, w: Column(seluk('tribunal_desizaun', c) if c == 'tribunal_desizaun_seluk' else c, css_class=f'form-group col-md-{w} mb-0')
		self.helper.layout = Layout(*[Row(*[cel(c, w) for c, w in row], css_class='form-row') for row in rows])

	def clean(self):
		cleaned = super().clean()
		if 'tribunal_desizaun_seluk' in self.fields and cleaned.get('tribunal_desizaun') != 'SELUK':
			cleaned['tribunal_desizaun_seluk'] = ''
		return cleaned


class AkompanamentuForm(forms.ModelForm):
	data = forms.DateField(label=_("Data"), widget=DateInput(), initial=timezone.localdate)

	class Meta:
		model = KazuAkompanamentu
		fields = ['data', 'asaun']
		widgets = {'asaun': forms.Textarea(attrs={'rows': 2, 'placeholder': _("Saida mak RbR halo? (vizita, reuniaun, karta, mediasaun…)")})}

	def __init__(self, *args, **kwargs):
		super(AkompanamentuForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		self.helper.layout = Layout(
			Row(
				Column('data', css_class='form-group col-md-3 mb-0'),
				Column('asaun', css_class='form-group col-md-9 mb-0'),
				css_class='form-row'
			),
		)

	def clean_data(self):
		d = self.cleaned_data['data']
		if d and d > timezone.localdate():
			raise forms.ValidationError(_('Data labele iha futuru.'))
		return d
