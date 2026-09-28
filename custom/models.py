from django.db import models
from django.utils.translation import gettext_lazy as _


class ActiveManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().filter(is_active=True)


class BaseModel(models.Model):
	code = models.CharField(max_length=30, unique=True, verbose_name=_("Kódigu"))
	name = models.CharField(max_length=150, verbose_name=_("Naran"))
	order = models.PositiveSmallIntegerField(default=0, verbose_name=_("Orden"))
	is_active = models.BooleanField(default=True, verbose_name=_("Ativu"))

	objects = models.Manager()
	active = ActiveManager()

	class Meta:
		abstract = True
		ordering = ['order', 'name']

	def __str__(self):
		return self.name


# ══════════════ WILAYAH (Munisípiu → Postu → Suku → Aldeia) ══════════════

class Munisipiu(BaseModel):
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

	class Meta(BaseModel.Meta):
		verbose_name = _("Munisípiu")
		verbose_name_plural = _("Munisípiu")


class PostuAdministrativu(BaseModel):
	munisipiu = models.ForeignKey(Munisipiu, on_delete=models.PROTECT, related_name='postu_set', verbose_name=_("Munisípiu"))

	class Meta(BaseModel.Meta):
		verbose_name = _("Postu Administrativu")
		verbose_name_plural = _("Postu Administrativu")


class Suku(BaseModel):
	postu = models.ForeignKey(PostuAdministrativu, on_delete=models.PROTECT, related_name='suku_set', verbose_name=_("Postu Administrativu"))
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

	class Meta(BaseModel.Meta):
		verbose_name = _("Suku")
		verbose_name_plural = _("Suku")


class Aldeia(BaseModel):
	suku = models.ForeignKey(Suku, on_delete=models.PROTECT, related_name='aldeia_set', verbose_name=_("Suku"))

	class Meta(BaseModel.Meta):
		verbose_name = _("Aldeia")
		verbose_name_plural = _("Aldeia")


# ══════════════ OPSAUN PADRONIZADU (Anexu A no E) ══════════════

class Pozisaun(BaseModel):
	class Meta(BaseModel.Meta):
		verbose_name = _("Pozisaun")
		verbose_name_plural = _("Pozisaun")


class TipuKonflitu(BaseModel):
	presiza_esplika = models.BooleanField(default=False, verbose_name=_("Presiza esplikasaun (Seluk)"))

	class Meta(BaseModel.Meta):
		verbose_name = _("Tipu Konflitu Rai")
		verbose_name_plural = _("Tipu Konflitu Rai")


class TipuRai(BaseModel):
	class Meta(BaseModel.Meta):
		verbose_name = _("Tipu Rai")
		verbose_name_plural = _("Tipu Rai")


class TipuEviksaun(BaseModel):
	class Meta(BaseModel.Meta):
		verbose_name = _("Tipu Eviksaun")
		verbose_name_plural = _("Tipu Eviksaun")


class TipuAtor(BaseModel):
	class Meta(BaseModel.Meta):
		verbose_name = _("Tipu Atór")
		verbose_name_plural = _("Tipu Atór")


class EstraguPatrimoniu(BaseModel):
	class Meta(BaseModel.Meta):
		verbose_name = _("Estragu Patrimóniu")
		verbose_name_plural = _("Estragu Patrimóniu")


class NesesidadeUrjente(BaseModel):
	class Meta(BaseModel.Meta):
		verbose_name = _("Nesesidade Urjente")
		verbose_name_plural = _("Nesesidade Urjente")
