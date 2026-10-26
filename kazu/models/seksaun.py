"""Seksaun kazu (tabela OneToOne ho Kazu). Kada seksaun = grupu pergunta ida iha formuláriu RbR.

Naran kampu hanesan ho uluk (iha Kazu): formuláriu, app offline, sinkron no Airtable la muda.
Atu aumenta seksaun foun:
    1. Kria classe iha ne'e ho `kazu = OneToOneField(Kazu, related_name='<naran>')`.
    2. Rejistu iha SEKSAUN (okos).
    3. `python manage.py makemigrations kazu`.
Kampu foun iha seksaun ne'ebé iha ona: aumenta field + makemigrations (la presiza muda Kazu).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from .kazu import Kazu
from .opsaun import SIN_LAE_CHOICES, ENTIDADE_CHOICES, RAI_UNIDADE_CHOICES


class SeksaunBase(models.Model):
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True

	def __str__(self):
		return f'{self._meta.verbose_name} · {self.kazu}'


class KazuFatin(SeksaunBase):
	# Detalla rai: enderesu, luan, poligon (fatin administrativu + GPS iha Kazu)
	kazu = models.OneToOneField(Kazu, on_delete=models.CASCADE, primary_key=True, related_name='fatin')
	enderesu_fatin = models.CharField(max_length=255, blank=True, verbose_name=_("Enderesu ka deskrisaun fatin"))
	rai_luan = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Rai nia luan"))
	rai_luan_unidade = models.CharField(max_length=2, choices=RAI_UNIDADE_CHOICES, default='M2', blank=True, verbose_name=_("Unidade"))
	# Poligon rai (GeoJSON FeatureCollection, bidang ida ka barak) — luan kalkula husi server (rumus hanesan Turf.js)
	poligon = models.JSONField(null=True, blank=True, verbose_name=_("Poligon rai"))
	poligon_luan_m2 = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name=_("Luan poligon (m²)"))
	poligon_keliling_m = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Haleu poligon (m)"))

	class Meta:
		verbose_name = _("Detalla Rai")
		verbose_name_plural = _("Detalla Rai")


class KazuEntidade(SeksaunBase):
	kazu = models.OneToOneField(Kazu, on_delete=models.CASCADE, primary_key=True, related_name='entidade')
	projetu = models.CharField(max_length=255, blank=True, verbose_name=_("Projetu (se Governu foti rai: atu hari'i saida?)"))
	entidade_foti = models.CharField(max_length=255, blank=True, verbose_name=_("Entidade ne'ebé foti rai"))
	entidade_kategoria = models.CharField(max_length=25, choices=ENTIDADE_CHOICES, blank=True, db_index=True, verbose_name=_("Entidade benefisiáriu (kategoria)"))
	entidade_kategoria_seluk = models.CharField(max_length=255, blank=True, verbose_name=_('Esplika entidade "Seluk"'))

	class Meta:
		verbose_name = _("Entidade ne'ebé foti rai")
		verbose_name_plural = _("Entidade ne'ebé foti rai")


class KazuPopulasaun(SeksaunBase):
	# Dadus jerál populasaun afetada (detalla kada grupu iha UmaKainAfetada)
	kazu = models.OneToOneField(Kazu, on_delete=models.CASCADE, primary_key=True, related_name='populasaun')
	iha_dadus_uma_kain = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Dadus uma-kain iha ka lae?"))
	fonte_dadus_uma_kain = models.CharField(max_length=150, blank=True, verbose_name=_("Fonte dadus uma-kain"))
	observasaun_afetadu = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba dadus ema afetadu"))

	class Meta:
		verbose_name = _("Populasaun Afetada")
		verbose_name_plural = _("Populasaun Afetada")


class KazuEviksaun(SeksaunBase):
	kazu = models.OneToOneField(Kazu, on_delete=models.CASCADE, primary_key=True, related_name='eviksaun')
	eviksaun_akontese = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, db_index=True, verbose_name=_("Eviksaun akontese ona?"))
	data_eviksaun = models.DateField(null=True, blank=True, verbose_name=_("Data eviksaun"))
	konsultasaun_molok = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Molok eviksaun iha konsultasaun ka lae?"))
	notifikasaun_klaru = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Molok eviksaun iha notifikasaun klaru ka lae?"))
	uza_forsa = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Durante eviksaun uza forsa ka lae?"))
	observasaun_eviksaun = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba eviksaun"))

	class Meta:
		verbose_name = _("Eviksaun")
		verbose_name_plural = _("Eviksaun")


class KazuPortavos(SeksaunBase):
	kazu = models.OneToOneField(Kazu, on_delete=models.CASCADE, primary_key=True, related_name='portavos')
	portavos_naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran portavós komunidade"))
	portavos_kontaktu = models.CharField(max_length=50, blank=True, verbose_name=_("Númeru kontaktu portavós"))
	portavos_observasaun = models.CharField(max_length=255, blank=True, verbose_name=_("Observasaun kona-ba portavós"))

	class Meta:
		verbose_name = _("Portavós Komunidade")
		verbose_name_plural = _("Portavós Komunidade")


# ══ Rejistu seksaun (fatin IDA) ══
SEKSAUN = {'fatin': KazuFatin, 'entidade': KazuEntidade, 'populasaun': KazuPopulasaun, 'eviksaun': KazuEviksaun, 'portavos': KazuPortavos}
SEKSAUN_REL = tuple(SEKSAUN)          # ba select_related('fatin', 'entidade', …)


def _instala():
	"""Kampu seksaun mosu iha Kazu hanesan property (lee/hakerek) + get_<kampu>_display."""
	for rel, model in SEKSAUN.items():
		Kazu.SEKSAUN[rel] = model
		for f in model._meta.concrete_fields:
			if f.name in ('kazu', 'updated_at'):
				continue
			if hasattr(Kazu, f.name):
				raise RuntimeError(f'Kampu {f.name} iha ona iha Kazu: naran kampu seksaun tenke úniku')
			Kazu.KAMPU_SEKSAUN[f.name] = rel

			def lee(self, _rel=rel, _f=f.name):
				return getattr(self.seksaun(_rel), _f)

			def hakerek(self, valor, _rel=rel, _f=f.name):
				setattr(self.seksaun(_rel), _f, valor)
				self._marka(_rel)

			setattr(Kazu, f.name, property(lee, hakerek))
			if f.choices:
				setattr(Kazu, f'get_{f.name}_display',
					lambda self, _rel=rel, _f=f.name: getattr(self.seksaun(_rel), f'get_{_f}_display')())


_instala()
