import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia, TipuKonflitu, TipuRai, \
	TipuEviksaun, TipuAtor, EstraguPatrimoniu, NesesidadeUrjente


# ══════════════ STATUS ══════════════
# Status Dadus (fluxu dadus: HP → server → verifikasaun)
DRAFT, ONGOING, PENDING = 'DRAFT', 'ONGOING', 'PENDING'
SYNCED, VERIFIED, APPROVED, COMPLETED = 'SYNCED', 'VERIFIED', 'APPROVED', 'COMPLETED'
REJECTED, CANCELED = 'REJECTED', 'CANCELED'

STATUS_CHOICES = [
	(DRAFT, _('Rascunho')),
	(ONGOING, _('Iha Terrenu')),
	(PENDING, _('Hein Sinál')),
	(SYNCED, _('Hein Verifikasaun')),
	(VERIFIED, _('Verifikadu')),
	(APPROVED, _('Aprovadu')),
	(COMPLETED, _('Remata')),
	(REJECTED, _('Rejeitadu')),
	(CANCELED, _('Kanseladu')),
]
# Opsaun husi formuláriu baze dadus sentrál RbR (Airtable) — Sin / Lae / La hatene
SIN, LAE, LAHATENE = 'SIN', 'LAE', 'LAHATENE'
SIN_LAE_CHOICES = [(SIN, _('Sin')), (LAE, _('Lae')), (LAHATENE, _('La hatene'))]

ENTIDADE_CHOICES = [
	('AJENSIA_AUTONOMU', _('Ajénsia Autónomu')), ('CCLN_VETERANU', _('CCLN-Veteranu')),
	('EMPREZA_PUBLIKU', _('Empreza Públiku')), ('GOVERNU', _('Governu')),
	('KOMPANIA_INTERNASIONAL', _('Kompañia Internasionál')), ('KOMPANIA_NASIONAL', _('Kompañia Nasionál')),
	('KONVENSAUN_RELIJIOZU', _('Konvensaun Relijiozu')), ('PARTIDU_POLITIKU', _('Partidu Polítiku')),
	('PNTL_FFDTL', _('PNTL / F-FDTL')), ('SELUK', _('Seluk')), ('LAHATENE', _('La hatene')),
]
RAI_UNIDADE_CHOICES = [('M2', _('Metru kuadradu (m²)')), ('HA', _('Hektar (ha)'))]

STATUS_EDITABLE = [DRAFT, ONGOING, PENDING, REJECTED]     # Investigadór bele edita
STATUS_SUBMITTED = [SYNCED, VERIFIED, APPROVED, COMPLETED]

# Status Kazu (prosesu kazu — Anexu A)
ABERTU, INVESTIGASAUN, AKSAUN_LEGAL, TAKA = 'ABERTU', 'INVESTIGASAUN', 'AKSAUN_LEGAL', 'TAKA'
STATUS_KAZU_CHOICES = [
	(ABERTU, _('Abertu')),
	(INVESTIGASAUN, _('Investigasaun')),
	(AKSAUN_LEGAL, _('Aksaun Legál')),
	(TAKA, _('Taka')),
]


def evidensia_path(instance, filename):
	ext = filename.rsplit('.', 1)[-1].lower()[:5]
	return f'kazu/{instance.kazu_id}/{uuid.uuid4().hex}.{ext}'


# ══════════════ KAZU (tabela sentrál) ══════════════
class Kazu(models.Model):
	# UUID: bele kria iha HP (offline) la iha risku ID bentrok
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	kode = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name=_("ID Kazu"))
	titulu = models.CharField(max_length=200, blank=True, verbose_name=_("Naran kazu"))
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT, db_index=True, verbose_name=_("Status Dadus"))
	status_kazu = models.CharField(max_length=15, choices=STATUS_KAZU_CHOICES, default=ABERTU, db_index=True, verbose_name=_("Status Kazu"))

	# Identifikasaun no lokalizasaun (A.2)
	data_relatoriu = models.DateField(null=True, blank=True, verbose_name=_("Data simu kazu iha RbR"))
	munisipiu = models.ForeignKey(Munisipiu, on_delete=models.PROTECT, related_name='kazu_set', verbose_name=_("Munisípiu"))
	postu = models.ForeignKey(PostuAdministrativu, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Postu Administrativu"))
	suku = models.ForeignKey(Suku, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Suku"))
	aldeia = models.ForeignKey(Aldeia, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Aldeia"))
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Latitude"))
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Longitude"))
	gps_akurasia = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Akurasia GPS (m)"))
	enderesu_fatin = models.CharField(max_length=255, blank=True, verbose_name=_("Enderesu ka deskrisaun fatin"))
	rai_luan = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Rai nia luan"))
	rai_luan_unidade = models.CharField(max_length=2, choices=RAI_UNIDADE_CHOICES, default='M2', blank=True, verbose_name=_("Unidade"))

	# Insidente (A.1)
	data_akontesimentu = models.DateField(null=True, blank=True, verbose_name=_("Data Akontesimentu"))
	tipu_konflitu = models.ManyToManyField(TipuKonflitu, blank=True, verbose_name=_("Tipu Konflitu Rai"))
	tipu_seluk = models.CharField(max_length=255, blank=True, verbose_name=_("Observasaun kona-ba tipu kazu"))
	tinan_disputa_hahu = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Tinan disputa hahú entre parte rua"))
	projetu = models.CharField(max_length=255, blank=True, verbose_name=_("Projetu (se Governu foti rai: atu hari'i saida?)"))
	entidade_foti = models.CharField(max_length=255, blank=True, verbose_name=_("Entidade ne'ebé foti rai"))
	entidade_kategoria = models.CharField(max_length=25, choices=ENTIDADE_CHOICES, blank=True, verbose_name=_("Entidade benefisiáriu (kategoria)"))
	tipu_rai = models.ForeignKey(TipuRai, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Tipu Rai"))
	deskrisaun = models.TextField(blank=True, verbose_name=_("Deskrisaun Insidente"))

	# Populasaun afetada (dadus jerál; detalla iha UmaKainAfetada)
	iha_dadus_uma_kain = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Dadus uma-kain iha ka lae?"))
	fonte_dadus_uma_kain = models.CharField(max_length=150, blank=True, verbose_name=_("Fonte dadus uma-kain"))
	observasaun_afetadu = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba dadus ema afetadu"))

	# Eviksaun
	eviksaun_akontese = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Eviksaun akontese ona?"))
	data_eviksaun = models.DateField(null=True, blank=True, verbose_name=_("Data eviksaun"))
	konsultasaun_molok = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Molok eviksaun iha konsultasaun ka lae?"))
	notifikasaun_klaru = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Molok eviksaun iha notifikasaun klaru ka lae?"))
	uza_forsa = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Durante eviksaun uza forsa ka lae?"))
	observasaun_eviksaun = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba eviksaun"))

	# Portavós komunidade
	portavos_naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran portavós komunidade"))
	portavos_kontaktu = models.CharField(max_length=50, blank=True, verbose_name=_("Númeru kontaktu portavós"))
	portavos_observasaun = models.CharField(max_length=255, blank=True, verbose_name=_("Observasaun kona-ba portavós"))

	# Estragu, urjente, konsentimentu (Anexu E)
	estragu = models.ManyToManyField(EstraguPatrimoniu, blank=True, verbose_name=_("Estragu Patrimóniu"))
	estragu_seluk = models.CharField(max_length=255, blank=True, verbose_name=_("Estragu seluk"))
	nesesidade = models.ManyToManyField(NesesidadeUrjente, blank=True, verbose_name=_("Nesesidade Urjente"))
	urjente = models.BooleanField(default=False, db_index=True, verbose_name=_("Urjente"))
	konsentimentu = models.BooleanField(default=False, verbose_name=_("Ema afetada fó konsentimentu informadu ba rekolla no uza dadus"))
	observasaun = models.TextField(blank=True, verbose_name=_("Observasaun Adisionál"))
	la_publika = models.BooleanField(default=False, verbose_name=_("La publika iha portal públiku"))

	# Import Excel (Admin): fatin GPS aproksimadu bainhira file la iha koordenada → Admin hadia iha mapa
	importasaun = models.ForeignKey('KazuImport', on_delete=models.SET_NULL, null=True, blank=True, related_name='kazu_set', verbose_name=_("Import"))
	gps_aproksimadu = models.BooleanField(default=False, verbose_name=_("GPS aproksimadu"))

	# Auditoria
	created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='kazu_created', verbose_name=_("Investigadór"))
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	synced_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Sinkron iha"))
	verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	verified_at = models.DateTimeField(null=True, blank=True)
	approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	approved_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-urjente', '-created_at']
		verbose_name = _("Kazu")
		verbose_name_plural = _("Kazu")
		permissions = [('verify_kazu', 'Bele verifika kazu'), ('approve_kazu', 'Bele aprova kazu')]

	def __str__(self):
		return self.kode or f'{_("Rascunho")} #{str(self.id)[:4].upper()}'

	@property
	def kode_display(self):
		return str(self)

	@property
	def is_editable(self):
		return self.status in STATUS_EDITABLE

	@property
	def total_afetadu(self):
		return sum(a.total_ema or 0 for a in self.afetadu.all())

	@property
	def total_uma_kain(self):
		return sum(a.uma_kain or 0 for a in self.afetadu.all())

	def foto_count(self):
		return self.evidensia.filter(tipu=Evidensia.FOTO).count()

	def video_count(self):
		return self.evidensia.filter(tipu=Evidensia.VIDEO).count()


class KazuSequence(models.Model):
	# Kontador ba kódigu kazu: SMKRE-<MUN>-<TINAN>-<NÚMERU>
	munisipiu = models.ForeignKey(Munisipiu, on_delete=models.CASCADE)
	tinan = models.PositiveSmallIntegerField()
	last = models.PositiveIntegerField(default=0)

	class Meta:
		unique_together = [('munisipiu', 'tinan')]


# ══════════════ A.3 UMA KAIN AFETADA ══════════════
class UmaKainAfetada(models.Model):
	kazu = models.ForeignKey(Kazu, on_delete=models.CASCADE, related_name='afetadu')
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
	kazu = models.ForeignKey(Kazu, on_delete=models.CASCADE, related_name='insidente')
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
	kazu = models.ForeignKey(Kazu, on_delete=models.CASCADE, related_name='ator')
	tipu_ator = models.ForeignKey(TipuAtor, on_delete=models.PROTECT, verbose_name=_("Tipu Atór"))
	naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran atór"))
	papel = models.CharField(max_length=255, blank=True, verbose_name=_("Papél iha insidente"))

	class Meta:
		verbose_name = _("Atór Envolvidu")
		verbose_name_plural = _("Atór Envolvidu")


# ══════════════ A.6 EVIDÉNSIA NO DOKUMENTU ══════════════
class Evidensia(models.Model):
	FOTO, VIDEO, DOKUMENTU, DEKLARASAUN = 'FOTO', 'VIDEO', 'DOKUMENTU', 'DEKLARASAUN'
	TIPU_CHOICES = [
		(FOTO, _('Foto')),
		(VIDEO, _('Vídeo')),
		(DOKUMENTU, _('Dokumentu Legál')),
		(DEKLARASAUN, _('Deklarasaun Testemuña')),
	]
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	kazu = models.ForeignKey(Kazu, on_delete=models.CASCADE, related_name='evidensia')
	tipu = models.CharField(max_length=12, choices=TIPU_CHOICES, verbose_name=_("Tipu"))
	file = models.FileField(upload_to=evidensia_path, verbose_name=_("File"))
	naran = models.CharField(max_length=150, blank=True, verbose_name=_("Naran dokumentu"))
	deskrisaun = models.CharField(max_length=255, blank=True, verbose_name=_("Deskrisaun"))
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Data upload"))

	class Meta:
		ordering = ['tipu', 'uploaded_at']
		verbose_name = _("Evidénsia")
		verbose_name_plural = _("Evidénsia")

	@property
	def is_image(self):
		return self.file.name.lower().rsplit('.', 1)[-1] in ('jpg', 'jpeg', 'png', 'webp')


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
	DESIZAUN_RBR_CHOICES = [('ARKIVU', _('Arkivu')), ('MONITORIZASAUN', _('Monitorizasaun')), ('ADVOKASIA', _('Advokasia ativu'))]

	kazu = models.OneToOneField(Kazu, on_delete=models.CASCADE, related_name='segimentu')
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
	tribunal_rejistu = models.CharField(max_length=10, choices=TRIBUNAL_CHOICES, blank=True, verbose_name=_("Rejistu iha tribunál?"))
	tribunal_data = models.DateField(null=True, blank=True, verbose_name=_("Data rejistu iha tribunál"))
	tribunal_representa = models.CharField(max_length=255, blank=True, verbose_name=_("Se mak rejistu ka reprezenta"))
	advogadu_kontaktu = models.CharField(max_length=255, blank=True, verbose_name=_("Kontaktu advogadu (naran, telefone, organizasaun)"))
	tribunal_observasaun = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba prosesu tribunál"))
	tribunal_desizaun = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Iha ona desizaun husi tribunál?"))
	tribunal_desizaun_data = models.DateField(null=True, blank=True, verbose_name=_("Data desizaun"))
	# Notifikasaun
	notif_simu = models.CharField(max_length=8, choices=SIN_LAE_CHOICES, blank=True, verbose_name=_("Simu notifikasaun ona?"))
	notif_data = models.DateField(null=True, blank=True, verbose_name=_("Data simu notifikasaun"))
	notif_husi = models.CharField(max_length=150, blank=True, verbose_name=_("Notifikasaun husi se?"))
	notif_observasaun = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba prosesu notifikasaun"))
	# Status no desizaun RbR
	data_ikus_cek = models.DateField(null=True, blank=True, verbose_name=_("Data ikus cek status kazu"))
	status_rezolusaun = models.CharField(max_length=20, choices=REZOLUSAUN_CHOICES, blank=True, verbose_name=_("Status rezolusaun kazu"))
	desizaun_rbr = models.CharField(max_length=15, choices=DESIZAUN_RBR_CHOICES, blank=True, verbose_name=_("Desizaun RbR ba kazu"))
	observasaun_kazu = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba kazu (desizaun RbR)"))

	updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = _("Segimentu Kazu")
		verbose_name_plural = _("Segimentu Kazu")


class KazuAkompanamentu(models.Model):
	# Rejistu akompañamentu kazu (lista: data + saida mak halo)
	kazu = models.ForeignKey(Kazu, on_delete=models.CASCADE, related_name='akompanamentu')
	data = models.DateField(verbose_name=_("Data"))
	asaun = models.TextField(verbose_name=_("Akompañamentu / asaun"))
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-data', '-created_at']
		verbose_name = _("Akompañamentu Kazu")
		verbose_name_plural = _("Akompañamentu Kazu")


# ══════════════ IMPORT EXCEL (Admin) ══════════════
class KazuImport(models.Model):
	# Kada upload Excel: pratinjau (RASCUNHO) → konfirma (REMATA). Rai liña hotu ba auditoria.
	RASCUNHO, REMATA, KANSELA = 'RASCUNHO', 'REMATA', 'KANSELA'
	STATUS_CHOICES = [(RASCUNHO, _('Pratinjau')), (REMATA, _('Importa ona')), (KANSELA, _('Kansela'))]
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	naran_file = models.CharField(max_length=255, verbose_name=_("File"))
	sha256 = models.CharField(max_length=64, db_index=True)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=RASCUNHO)
	dadus = models.JSONField(default=list)                     # liña validadu (pratinjau)
	total = models.PositiveIntegerField(default=0)
	total_ok = models.PositiveIntegerField(default=0)
	total_aproksimadu = models.PositiveIntegerField(default=0)
	created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', verbose_name=_("Admin"))
	created_at = models.DateTimeField(auto_now_add=True)
	konfirma_iha = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']
		verbose_name = _("Import Kazu")
		verbose_name_plural = _("Import Kazu")

	def __str__(self):
		return self.naran_file

	@property
	def total_erru(self):
		return self.total - self.total_ok


# ══════════════ ISTÓRIA (se, bainhira, razaun) ══════════════
class KazuHistoria(models.Model):
	DADUS, KAZU, EDITA, LEE = 'DADUS', 'KAZU', 'EDITA', 'LEE'
	TIPU_CHOICES = [(DADUS, _('Status Dadus')), (KAZU, _('Status Kazu')), (EDITA, _('Edita')), (LEE, _('Lee'))]
	kazu = models.ForeignKey(Kazu, on_delete=models.CASCADE, related_name='historia')
	tipu = models.CharField(max_length=6, choices=TIPU_CHOICES, default=DADUS)
	status_antes = models.CharField(max_length=15, blank=True)
	status_foun = models.CharField(max_length=15, blank=True)
	nota = models.TextField(blank=True, verbose_name=_("Razaun / Nota"))
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		verbose_name = _("Istória Kazu")
		verbose_name_plural = _("Istória Kazu")

	def status_antes_label(self):
		return dict(STATUS_CHOICES + STATUS_KAZU_CHOICES).get(self.status_antes, self.status_antes)

	def status_foun_label(self):
		return dict(STATUS_CHOICES + STATUS_KAZU_CHOICES).get(self.status_foun, self.status_foun)
