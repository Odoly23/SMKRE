"""Lista laran kazu: uma-kain afetada, insidente eviksaun, atór envolvidu."""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from custom.models import TipuEviksaun, TipuAtor


# ══════════════ A.3 UMA KAIN AFETADA ══════════════
class UmaKainAfetada(models.Model):
	kazu = models.ForeignKey('kazu.Kazu', on_delete=models.CASCADE, related_name='afetadu')
	uma_kain = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Númeru Uma-Kain"))
	total_ema = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Estimasaun Total Ema"))
	mane = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Mane"))
	feto = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Feto"))
	labarik = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Labarik"))
	katuas_ferik = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Idozu (tinan 60 ba leten)"))
	defisiensia = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Ema ho Defisiénsia"))

	class Meta:
		verbose_name = _("Uma-Kain Afetada")
		verbose_name_plural = _("Uma-Kain Afetada")


# ══════════════ A.4 INSIDENTE DESLOKAMENTU / EVIKSAUN ══════════════
class InsidenteEviksaun(models.Model):
	kazu = models.ForeignKey('kazu.Kazu', on_delete=models.CASCADE, related_name='insidente')
	tipu_eviksaun = models.ForeignKey(TipuEviksaun, on_delete=models.PROTECT, verbose_name=_("Tipu Eviksaun"))
	loron_avizu = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Loron avizu antes eviksaun"))
	forsa_seguransa = models.BooleanField(default=False, verbose_name=_("Forsa seguransa prezente"))
	estragu = models.CharField(max_length=255, blank=True, verbose_name=_("Estragu (uma / to'os / sasán)"))
	deskrisaun = models.TextField(blank=True, verbose_name=_("Narrativu"))

	class Meta:
		verbose_name = _("Insidente Eviksaun")
		verbose_name_plural = _("Insidente Eviksaun")


# ══════════════ A.5 ATÓR ENVOLVIDU ══════════════
class AtorEnvolvidu(models.Model):
	kazu = models.ForeignKey('kazu.Kazu', on_delete=models.CASCADE, related_name='ator')
	tipu_ator = models.ForeignKey(TipuAtor, on_delete=models.PROTECT, verbose_name=_("Tipu Atór"))
	naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran atór"))
	papel = models.CharField(max_length=255, blank=True, verbose_name=_("Papél iha insidente"))

	class Meta:
		verbose_name = _("Atór Envolvidu")
		verbose_name_plural = _("Atór Envolvidu")

