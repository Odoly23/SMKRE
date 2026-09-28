import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from kazu.models import Kazu


def vault_path(instance, filename):
	# File vault: naran aleatóriu (la hatudu naran orijinál iha disku). Asesu liuhusi view download deit.
	ext = filename.rsplit('.', 1)[-1].lower()[:5] if '.' in filename else 'bin'
	folder = instance.kazu_id or 'jeral'
	return f'legal/{folder}/{uuid.uuid4().hex}.{ext}'


# ══════════════ DOKUMENTU LEGÁL (Document Vault) ══════════════
class DokumentuLegal(models.Model):
	KARTA, DEKLARASAUN, SERTIFIKADU, DESIZAUN, KONTRATU, LEI, SELUK = \
		'KARTA', 'DEKLARASAUN', 'SERTIFIKADU', 'DESIZAUN', 'KONTRATU', 'LEI', 'SELUK'
	KATEGORIA_CHOICES = [
		(KARTA, _('Karta / Reklamasaun')),
		(DEKLARASAUN, _('Deklarasaun Testemuña')),
		(SERTIFIKADU, _('Sertifikadu / Títulu Rai')),
		(DESIZAUN, _('Desizaun Tribunál / Autoridade')),
		(KONTRATU, _('Kontratu / Akordu')),
		(LEI, _('Lei / Regulamentu')),
		(SELUK, _('Seluk')),
	]
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	kazu = models.ForeignKey(Kazu, on_delete=models.PROTECT, null=True, blank=True, related_name='dokumentu_legal',
		verbose_name=_("Kazu"), help_text=_("Mamuk = dokumentu jerál (lei, regulamentu)"))
	kategoria = models.CharField(max_length=12, choices=KATEGORIA_CHOICES, verbose_name=_("Kategoria"))
	titulu = models.CharField(max_length=200, verbose_name=_("Títulu dokumentu"))
	deskrisaun = models.TextField(blank=True, verbose_name=_("Deskrisaun"))
	data_dokumentu = models.DateField(null=True, blank=True, verbose_name=_("Data dokumentu"))
	konfidensial = models.BooleanField(default=False, verbose_name=_("Konfidensiál"),
		help_text=_("Ofisiál Legál no Superadmin deit mak bele haree"))

	# File + integridade
	file = models.FileField(upload_to=vault_path, verbose_name=_("File"))
	naran_orijinal = models.CharField(max_length=200, blank=True)
	tamanu = models.PositiveIntegerField(default=0)
	sha256 = models.CharField(max_length=64, blank=True, verbose_name=_("SHA-256"))

	# Versaun: versaun foun troka versaun tuan (tuan la hamoos, hela iha istória)
	versaun = models.PositiveSmallIntegerField(default=1, verbose_name=_("Versaun"))
	versaun_anterior = models.OneToOneField('self', on_delete=models.PROTECT, null=True, blank=True, related_name='versaun_foun')
	atual = models.BooleanField(default=True, db_index=True)

	# Arkivu (la hamoos: rai ba auditoria)
	arkivadu = models.BooleanField(default=False, db_index=True)
	arkivu_razaun = models.CharField(max_length=255, blank=True)
	arkivu_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	arkivu_at = models.DateTimeField(null=True, blank=True)

	uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+', verbose_name=_("Upload husi"))
	uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Data upload"))

	class Meta:
		ordering = ['-uploaded_at']
		verbose_name = _("Dokumentu Legál")
		verbose_name_plural = _("Dokumentu Legál")

	def __str__(self):
		return f'{self.titulu} (v{self.versaun})'

	@property
	def ext(self):
		return self.file.name.rsplit('.', 1)[-1].lower() if '.' in self.file.name else ''

	def historia_versaun(self):
		# Versaun hotu (foun → tuan)
		lista, doc = [], self
		while doc:
			lista.append(doc)
			doc = doc.versaun_anterior
		return lista


# ══════════════ NOTA LEGÁL (análize, konsellu, audiénsia, prazu) ══════════════
class NotaLegal(models.Model):
	ANALIZE, KONSELLU, MEDIASAUN, AUDIENSIA, AKSAUN = 'ANALIZE', 'KONSELLU', 'MEDIASAUN', 'AUDIENSIA', 'AKSAUN'
	TIPU_CHOICES = [
		(ANALIZE, _('Análize Legál')),
		(KONSELLU, _('Konsellu ba Komunidade')),
		(MEDIASAUN, _('Mediasaun')),
		(AUDIENSIA, _('Audiénsia / Tribunál')),
		(AKSAUN, _('Aksaun Seluk')),
	]
	kazu = models.ForeignKey(Kazu, on_delete=models.PROTECT, related_name='nota_legal', verbose_name=_("Kazu"))
	tipu = models.CharField(max_length=10, choices=TIPU_CHOICES, verbose_name=_("Tipu"))
	testu = models.TextField(verbose_name=_("Nota"))
	prazu = models.DateField(null=True, blank=True, verbose_name=_("Prazu / Data audiénsia"),
		help_text=_("Sistema sei haruka lembrete loron 3 antes"))
	remata = models.BooleanField(default=False, verbose_name=_("Remata"))
	konfidensial = models.BooleanField(default=False, verbose_name=_("Konfidensiál"))
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['remata', 'prazu', '-created_at']
		verbose_name = _("Nota Legál")
		verbose_name_plural = _("Nota Legál")

	def __str__(self):
		return f'{self.get_tipu_display()} · {self.kazu}'

	@property
	def atrazu(self):
		return bool(self.prazu and not self.remata and self.prazu < timezone.localdate())


# ══════════════ AUDITORIA ASESU VAULT ══════════════
class AsesuVault(models.Model):
	UPLOAD, DOWNLOAD, VERSAUN, ARKIVU = 'UPLOAD', 'DOWNLOAD', 'VERSAUN', 'ARKIVU'
	AKSAUN_CHOICES = [(UPLOAD, _('Upload')), (DOWNLOAD, _('Download')), (VERSAUN, _('Versaun foun')), (ARKIVU, _('Arkivu'))]
	dokumentu = models.ForeignKey(DokumentuLegal, on_delete=models.PROTECT, related_name='asesu')
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	aksaun = models.CharField(max_length=10, choices=AKSAUN_CHOICES)
	ip = models.GenericIPAddressField(null=True, blank=True)
	at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-at']
		verbose_name = _("Asesu Vault")
		verbose_name_plural = _("Asesu Vault")
