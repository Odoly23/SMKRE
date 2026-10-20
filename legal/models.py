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


# ══════════════ SURVEI LEGÁL (Perguntas Xave Sira Legal) ══════════════
SIN_LAE = [('SIN', _('Sin')), ('LAE', _('Lae'))]


def survei_path(instance, filename):
	ext = filename.rsplit('.', 1)[-1].lower()[:5] if '.' in filename else 'bin'
	return f'legal/survei/{instance.survei_id}/{uuid.uuid4().hex}.{ext}'


class SurveiSequence(models.Model):
	# Kontador ba kódigu survei: LGL-<MUN>-<TINAN>-<NNNN>
	munisipiu = models.ForeignKey('custom.Munisipiu', on_delete=models.CASCADE)
	tinan = models.PositiveSmallIntegerField()
	last = models.PositiveIntegerField(default=0)

	class Meta:
		unique_together = ('munisipiu', 'tinan')


class SurveiLegal(models.Model):
	RASCUNHO, HARUKA, VERIFIKADU, REJEITADU = 'RASCUNHO', 'HARUKA', 'VERIFIKADU', 'REJEITADU'
	STATUS_CHOICES = [(RASCUNHO, _('Rascunho')), (HARUKA, _('Hein Verifikasaun')), (VERIFIKADU, _('Verifikadu')), (REJEITADU, _('Rejeitadu'))]
	STATUS_EDITABLE = (RASCUNHO, REJEITADU)
	SEXU_CHOICES = [('MANE', _('Mane')), ('FETO', _('Feto'))]
	ESTADU_CIVIL_CHOICES = [('SOLTEIRU', _('Solteiru/a')), ('KABEN', _('Kaben')), ('VIUVU', _('Viúvu/a')),
		('DIVORSIADU', _('Divorsiadu/a')), ('SELUK', _('Seluk'))]
	INSTITUISAUN_CHOICES = [('PUBLIKU', _('Publiku')), ('PRIVADU', _('Privadu'))]
	ERANSA, SOSA, FOO, POSSE = 'ERANSA', 'SOSA', 'FOO', 'POSSE'
	MEIUS_CHOICES = [(SOSA, _('Sosa')), (FOO, _('Foó ka Doasaun')), (ERANSA, _('Eransa')), (POSSE, _('Posse / Okupa'))]
	HALO_SE_CHOICES = [('RASIK', _('Halo rasik')), ('EMA_SELUK', _('Ema seluk mak halo'))]
	DOK_IDENTIFIKASAUN = [('KARTAUN_ELEITORAL', _('Kartaun Eleitoral')), ('BI', _('Bileti Identidade')), ('PASSAPORTE', _('Passaporte'))]
	DOK_RELEVANTE = [('DEKLARASAUN_SOSA', _('Deklarasaun sosa no faan')), ('NOTIFIKASAUN', _('Notifikasaun')), ('DESPASHO', _('Despasho')),
		('NUIP', _('NUIP (Numeru Uniku Identifikasaun Parcela)')), ('MAPA', _('Mapa rai nian'))]
	FOTOGRAFIA = [('TOOS', _("To'os")), ('NATAR', _('Natar')), ('KANTADEIRO', _('Kantadeiro')), ('AIHORIS', _('Aihoris')),
		('BALIZA', _('Baliza')), ('FATUK_HADA', _('Fatuk hada')), ('AIBOSSA', _('Aibossa')), ('RATE', _('Rate')),
		('BEE_MATAN', _('Beé matan')), ('FATIN_LULIK', _('Fatin lulik')), ('UMA', _('Uma')), ('KIOS', _('Kios'))]

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)   # bele kria iha HP (offline)
	kode = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name=_("ID Survei"))
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=RASCUNHO, db_index=True, verbose_name=_("Status"))
	# Kazu SIBAR ne'ebé iha ona (opsionál) — mamuk = kazu legál foun ho fatin rasik
	kazu = models.ForeignKey(Kazu, on_delete=models.PROTECT, null=True, blank=True, related_name='survei_legal', verbose_name=_("Kazu SIBAR"))
	titulu = models.CharField(max_length=200, blank=True, verbose_name=_("Naran kazu legál"))
	data_survei = models.DateField(default=timezone.localdate, verbose_name=_("Data survei"))
	munisipiu = models.ForeignKey('custom.Munisipiu', on_delete=models.PROTECT, related_name='+', verbose_name=_("Munisipiu"))
	postu = models.ForeignKey('custom.PostuAdministrativu', on_delete=models.PROTECT, null=True, blank=True, related_name='+', verbose_name=_("Postu Administrativu"))
	suku = models.ForeignKey('custom.Suku', on_delete=models.PROTECT, null=True, blank=True, related_name='+', verbose_name=_("Suku"))
	aldeia = models.ForeignKey('custom.Aldeia', on_delete=models.PROTECT, null=True, blank=True, related_name='+', verbose_name=_("Aldeia"))
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Latitude"))
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Longitude"))
	gps_akurasia = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Akurasia GPS (m)"))

	# I. Identifikasaun parte (disputante)
	parte_naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran"))
	parte_sexu = models.CharField(max_length=4, choices=SEXU_CHOICES, blank=True, verbose_name=_("Sexu/Generu"))
	parte_data_moris = models.DateField(null=True, blank=True, verbose_name=_("Data Moris"))
	parte_estadu_civil = models.CharField(max_length=12, choices=ESTADU_CIVIL_CHOICES, blank=True, verbose_name=_("Estadu civil"))
	parte_hela_fatin = models.CharField(max_length=255, blank=True, verbose_name=_("Hela Fatin"))
	parte_kartaun_eleitoral = models.CharField(max_length=50, blank=True, verbose_name=_("Nu kartaun Eleitoral"))
	parte_profisaun = models.CharField(max_length=100, blank=True, verbose_name=_("Profisaun"))
	parte_kontaktu = models.CharField(max_length=50, blank=True, verbose_name=_("Numeru Kontaktu"))
	parte_ehd = models.CharField(max_length=3, choices=SIN_LAE, blank=True, verbose_name=_("EhD ka lae?"),
		help_text=_("Ema ho defisiénsia"))

	# II. Entidade ne'ebé atu foti rai
	entidade_naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran"))
	entidade_kontaktu = models.CharField(max_length=50, blank=True, verbose_name=_("Numeru Kontaktu"))
	entidade_instituisaun = models.CharField(max_length=8, choices=INSTITUISAUN_CHOICES, blank=True, verbose_name=_("Instituisaun Publiku/Privadu"))
	entidade_enderesu = models.CharField(max_length=255, blank=True, verbose_name=_("Domisiliu/enderesu"))

	# III. Perguntas xave: meius ka maneira hetan rai
	meius = models.CharField(max_length=8, choices=MEIUS_CHOICES, blank=True, verbose_name=_("Meius ka maneira hetan rai"))
	# 1. Eransa (antesessor mate ona)
	eransa_husi_se = models.CharField(max_length=255, blank=True, verbose_name=_("Rai no uma ne'e hetan husi se?"))
	eransa_relasaun = models.TextField(blank=True, verbose_name=_("Deskrisaun relasaun oinsa toó iha ita boot?"))
	eransa_herdeiru = models.TextField(blank=True, verbose_name=_("Identifikasaun ba herdeiru sira?"))
	eransa_rai_seluk = models.CharField(max_length=3, choices=SIN_LAE, blank=True, verbose_name=_("Rai nebeé mak disputa iha ka lae antesessor nia rai seluk?"))
	eransa_fahe = models.CharField(max_length=3, choices=SIN_LAE, blank=True, verbose_name=_("Eransa ne'e fahe ona ka seidauk?"))
	eransa_fahe_ba_se = models.TextField(blank=True, verbose_name=_("Fahe ona ba se?"))
	eransa_fahe_lokalizasaun = models.TextField(blank=True, verbose_name=_("Identifikasaun/lokalizasaun rai/uma seluk nebeé fahe ona?"))
	eransa_fahe_desde = models.CharField(max_length=100, blank=True, verbose_name=_("Fahe desde horibainhira?"))
	# 2. Sosa
	sosa_husi_se = models.CharField(max_length=255, blank=True, verbose_name=_("Sosa husi se?"))
	sosa_folin = models.CharField(max_length=100, blank=True, verbose_name=_("Folin hira?"))
	sosa_bainhira = models.CharField(max_length=100, blank=True, verbose_name=_("Sosa bainhira?"))
	sosa_halo_saida = models.TextField(blank=True, verbose_name=_("Depois de sosa halo saida iha rai nia leten?"))
	sosa_halo_desde = models.CharField(max_length=100, blank=True, verbose_name=_("Halo desde iha sa tinan?"))
	sosa_halo_se = models.CharField(max_length=10, choices=HALO_SE_CHOICES, blank=True, verbose_name=_("Ema seluk mak halo ka halo rasik?"))
	sosa_akordu = models.CharField(max_length=3, choices=SIN_LAE, blank=True, verbose_name=_("Akordu iha ka lae?"))
	sosa_akordu_fatin = models.CharField(max_length=255, blank=True, verbose_name=_("Halo akordu iha ne'ebe?"))
	sosa_sasin = models.CharField(max_length=3, choices=SIN_LAE, blank=True, verbose_name=_("Sasin iha ka lae?"))
	sasin_1 = models.CharField(max_length=150, blank=True, verbose_name=_("Sasin 1"))
	sasin_2 = models.CharField(max_length=150, blank=True, verbose_name=_("Sasin 2"))
	sasin_3 = models.CharField(max_length=150, blank=True, verbose_name=_("Sasin 3"))
	sasin_4 = models.CharField(max_length=150, blank=True, verbose_name=_("Sasin 4"))
	# 3. Foó / doasaun (bele família ka ema seluk)
	foo_se = models.CharField(max_length=255, blank=True, verbose_name=_("Semak foó?"))
	foo_bainhira = models.CharField(max_length=100, blank=True, verbose_name=_("Foó horibainhira?"))
	foo_akordu = models.CharField(max_length=3, choices=SIN_LAE, blank=True, verbose_name=_("Akordu iha ka lae?"))
	foo_akordu_fatin = models.CharField(max_length=255, blank=True, verbose_name=_("Halo akordu iha ne'ebe?"))
	foo_relasaun = models.TextField(blank=True, verbose_name=_("Oinsa ita nia relasaun ho ema nebeé mak foó?"))
	# 4. Posse / okupa
	posse_hahu = models.CharField(max_length=100, blank=True, verbose_name=_("Hahu hela / okupa bainhira?"))
	posse_halo_saida = models.TextField(blank=True, verbose_name=_("Halo saida iha rai ne'e nia leten?"))
	posse_se_mak_halo = models.CharField(max_length=255, blank=True, verbose_name=_("Semak halo?"))
	posse_periodu = models.CharField(max_length=100, blank=True, verbose_name=_("Hahu horibainhira to'o bainhira?"))
	posse_ema_seluk_tinan = models.CharField(max_length=100, blank=True, verbose_name=_("Se ema seluk mak halo husi sa tinan to'o sa tinan"))
	posse_relasaun_sosa = models.TextField(blank=True, verbose_name=_("Relasaun ho ema ne'ebe mak sosa rai ka uma neé oinsa?"))
	posse_uza_rai = models.TextField(blank=True, verbose_name=_("Uza rai ne'e ba halo saida?"))
	posse_luan_rai = models.CharField(max_length=100, blank=True, verbose_name=_("Rai tomak neé nia luan hira?"))
	posse_luan_disputa = models.CharField(max_length=100, blank=True, verbose_name=_("Rai ne'ebe mak disputa luan hira?"))
	posse_luan_uma = models.CharField(max_length=100, blank=True, verbose_name=_("Uma nia luan hira?"))

	# Notas importante (checklist dokumentu no fotografia)
	dok_identifikasaun = models.JSONField(default=list, blank=True, verbose_name=_("Dokumentus identifikasaun"))
	dok_relevante = models.JSONField(default=list, blank=True, verbose_name=_("Dokumentus relevante sira seluk"))
	fotografia = models.JSONField(default=list, blank=True, verbose_name=_("Fotografia"))
	observasaun = models.TextField(blank=True, verbose_name=_("Observasaun"))

	nota_rejeita = models.CharField(max_length=255, blank=True, verbose_name=_("Razaun rejeita"))
	created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='survei_legal', verbose_name=_("Ofisiál Legál"))
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	haruka_at = models.DateTimeField(null=True, blank=True)
	verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	verified_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']
		verbose_name = _("Survei Legál")
		verbose_name_plural = _("Survei Legál")

	def __str__(self):
		return self.kode or self.titulu or str(self.pk)[:8]

	@property
	def editable(self):
		return self.status in self.STATUS_EDITABLE

	def label_lista(self, campo):
		opsaun = dict(getattr(self, {'dok_identifikasaun': 'DOK_IDENTIFIKASAUN', 'dok_relevante': 'DOK_RELEVANTE', 'fotografia': 'FOTOGRAFIA'}[campo]))
		return [str(opsaun.get(c, c)) for c in getattr(self, campo) or []]


class SurveiLegalFile(models.Model):
	FOTO, DOKUMENTU = 'FOTO', 'DOKUMENTU'
	TIPU_CHOICES = [(FOTO, _('Foto')), (DOKUMENTU, _('Dokumentu'))]
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)   # ID husi HP (upload idempotente)
	survei = models.ForeignKey(SurveiLegal, on_delete=models.CASCADE, related_name='files')
	tipu = models.CharField(max_length=10, choices=TIPU_CHOICES, verbose_name=_("Tipu"))
	file = models.FileField(upload_to=survei_path, verbose_name=_("File"))
	naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran / deskrisaun"))
	uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['uploaded_at']

	@property
	def is_image(self):
		return self.file.name.lower().rsplit('.', 1)[-1] in ('jpg', 'jpeg', 'png', 'webp')
