"""Segimentu kazu (eskritóriu RbR): tribunál, notifikasaun, status no akompañamentu."""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from .opsaun import SIN_LAE_CHOICES, DESIZAUN_RBR_CHOICES as _DESIZAUN


# ══════════════ SEGIMENTU KAZU (eskritóriu: tribunál, notifikasaun, status rezolusaun) ══════════════
class KazuSegimentu(models.Model):
	# Dadus akompañamentu ne'ebé eskritóriu RbR atualiza durante kazu nia moris (la'ós Investigadór)
	FOKAL_TIPU_CHOICES = [('MEMBRU', _('Membru')), ('MEMBRU_LA_ATIVU', _("Membru ne'ebé la ativu ona")),
		('MEMBRU_SEKRETARIADU', _('Membru no Sekretariadu')), ('SEKRETARIADU', _('Sekretariadu RbR')), ('LAHATENE', _('La hatene'))]
	TRIBUNAL_CHOICES = [('LAE', _('Lae')), ('SIN', _('Sin')), ('LAHATENE', _('La hatene')), ('DADAUN', _('Agora dadaun rejistu hela iha tribunál'))]
	REZOLUSAUN_CHOICES = [
		('ABANDONA', _('Abandona')), ('BALU_RESOLVE', _('Claim balu resolve, balu seidauk')),
		('LAHATENE', _('La hatene status atuál')), ('RES_FAMILIA', _('Resolve ona - Família deit')),
		('RES_TRIBUNAL', _('Resolve ona - Iha tribunál')), ('RES_MEDIASAUN', _('Resolve ona - Liuhusi mediasaun')),
		('RES_ABANDONA', _('Resolve ona - Parte seluk abandona disputa')), ('RES_KOMPENSASAUN', _('Resolve ona - Simu kompensasaun')),
		('SEIDAUK', _('Seidauk resolve')),
	]
	TRIBUNAL_DESIZAUN_CHOICES = SIN_LAE_CHOICES + [('SELUK', _('Seluk'))]
	DESIZAUN_RBR_CHOICES = _DESIZAUN

	kazu = models.OneToOneField('kazu.Kazu', on_delete=models.CASCADE, related_name='segimentu')
	# Fokal point RbR
	fokal_naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran fokal point RbR"))
	fokal_telemovel = models.CharField(max_length=50, blank=True, verbose_name=_("Númeru telemóvel fokal point"))
	fokal_organizasaun = models.CharField(max_length=150, blank=True, verbose_name=_("Organizasaun"))
	fokal_enderesu = models.CharField(max_length=255, blank=True, verbose_name=_("Enderesu organizasaun"))
	fokal_tipu = models.CharField(max_length=20, choices=FOKAL_TIPU_CHOICES, blank=True, verbose_name=_("Tipu fokal point"))
	# Organizasaun seluk ne'ebé akompaña
	org_seluk = models.CharField(max_length=150, blank=True, verbose_name=_("Organizasaun seluk ne'ebé akompaña"))
	org_seluk_naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran ema husi organizasaun seluk"))
	org_seluk_kontaktu = models.CharField(max_length=50, blank=True, verbose_name=_("Númeru kontaktu (organizasaun seluk)"))
	# Tribunál
	tribunal_rejistu = models.CharField(max_length=10, choices=TRIBUNAL_CHOICES, blank=True, db_index=True, verbose_name=_("Rejistu iha tribunál?"))
	tribunal_data = models.DateField(null=True, blank=True, verbose_name=_("Data rejistu iha tribunál"))
	tribunal_representa = models.CharField(max_length=255, blank=True, verbose_name=_("Se mak rejistu ka reprezenta"))
	advogadu_kontaktu = models.CharField(max_length=255, blank=True, verbose_name=_("Kontaktu advogadu (naran, telefone, organizasaun)"))
	tribunal_observasaun = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba prosesu tribunál"))
	tribunal_desizaun = models.CharField(max_length=8, choices=TRIBUNAL_DESIZAUN_CHOICES, blank=True, verbose_name=_("Iha ona desizaun husi tribunál?"))
	tribunal_desizaun_seluk = models.CharField(max_length=255, blank=True, verbose_name=_('Esplika desizaun tribunál "Seluk"'))
	tribunal_desizaun_data = models.DateField(null=True, blank=True, verbose_name=_("Data desizaun"))
	# Notifikasaun
	notif_simu = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Simu notifikasaun ona?"))
	notif_data = models.DateField(null=True, blank=True, verbose_name=_("Data simu notifikasaun"))
	notif_husi = models.CharField(max_length=150, blank=True, verbose_name=_("Notifikasaun husi se?"))
	notif_observasaun = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba prosesu notifikasaun"))
	# Status no desizaun RbR
	data_ikus_cek = models.DateField(null=True, blank=True, verbose_name=_("Data ikus cek status kazu"))
	status_rezolusaun = models.CharField(max_length=20, choices=REZOLUSAUN_CHOICES, blank=True, db_index=True, verbose_name=_("Status rezolusaun kazu"))
	desizaun_rbr = models.CharField(max_length=15, choices=DESIZAUN_RBR_CHOICES, blank=True, verbose_name=_("Desizaun RbR ba kazu"))
	observasaun_kazu = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba kazu (desizaun RbR)"))

	updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = _("Segimentu Kazu")
		verbose_name_plural = _("Segimentu Kazu")


class KazuAkompanamentu(models.Model):
	# Rejistu akompañamentu kazu (lista: data + saida mak halo)
	kazu = models.ForeignKey('kazu.Kazu', on_delete=models.CASCADE, related_name='akompanamentu')
	data = models.DateField(verbose_name=_("Data"))
	asaun = models.TextField(verbose_name=_("Akompañamentu / asaun"))
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-data', '-created_at']
		verbose_name = _("Akompañamentu Kazu")
		verbose_name_plural = _("Akompañamentu Kazu")
