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
	titulu = models.CharField(max_length=200, blank=True, verbose_name=_("Títulu kazu"))
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT, db_index=True, verbose_name=_("Status Dadus"))
	status_kazu = models.CharField(max_length=15, choices=STATUS_KAZU_CHOICES, default=ABERTU, db_index=True, verbose_name=_("Status Kazu"))

	# Identifikasaun no lokalizasaun (A.2)
	data_relatoriu = models.DateField(null=True, blank=True, verbose_name=_("Data Relatóriu"))
	munisipiu = models.ForeignKey(Munisipiu, on_delete=models.PROTECT, related_name='kazu_set', verbose_name=_("Munisípiu"))
	postu = models.ForeignKey(PostuAdministrativu, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Postu Administrativu"))
	suku = models.ForeignKey(Suku, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Suku"))
	aldeia = models.ForeignKey(Aldeia, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Aldeia"))
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Latitude"))
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Longitude"))
	gps_akurasia = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Akurasia GPS (m)"))

	# Insidente (A.1)
	data_akontesimentu = models.DateField(null=True, blank=True, verbose_name=_("Data Akontesimentu"))
	tipu_konflitu = models.ManyToManyField(TipuKonflitu, blank=True, verbose_name=_("Tipu Konflitu Rai"))
	tipu_seluk = models.CharField(max_length=255, blank=True, verbose_name=_("Seluk: favor esplika"))
	tipu_rai = models.ForeignKey(TipuRai, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Tipu Rai"))
	deskrisaun = models.TextField(blank=True, verbose_name=_("Deskrisaun Insidente"))

	# Estragu, urjente, konsentimentu (Anexu E)
	estragu = models.ManyToManyField(EstraguPatrimoniu, blank=True, verbose_name=_("Estragu Patrimóniu"))
	estragu_seluk = models.CharField(max_length=255, blank=True, verbose_name=_("Estragu seluk"))
	nesesidade = models.ManyToManyField(NesesidadeUrjente, blank=True, verbose_name=_("Nesesidade Urjente"))
	urjente = models.BooleanField(default=False, db_index=True, verbose_name=_("Urjente"))
	konsentimentu = models.BooleanField(default=False, verbose_name=_("Ema afetada fó konsentimentu informadu ba rekolla no uza dadus"))
	observasaun = models.TextField(blank=True, verbose_name=_("Observasaun Adisionál"))
	la_publika = models.BooleanField(default=False, verbose_name=_("La publika iha portal públiku"))

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
	katuas_ferik = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Katuas-Ferik"))
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
