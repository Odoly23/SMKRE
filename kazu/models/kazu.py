"""Kazu: tabela sentrál (identifikasaun, fatin administrativu, status, auditoria).

Detalla ne'ebé la uza beibeik iha buka/filtru rai iha tabela OneToOne (haree seksaun.py):
    kazu.fatin       → KazuFatin       (enderesu, luan rai, poligon)
    kazu.entidade    → KazuEntidade    (projetu, entidade ne'ebé foti rai)
    kazu.populasaun  → KazuPopulasaun  (dadus uma-kain)
    kazu.eviksaun    → KazuEviksaun    (detalla eviksaun)
    kazu.portavos    → KazuPortavos    (portavós komunidade)

Kompatibilidade: kampu seksaun bele lee/hakerek iha kazu direta (kazu.eviksaun_akontese = 'SIN'; kazu.save()).
Iha ORM (filter/exclude/order_by) uza naran relasaun: Kazu.objects.filter(eviksaun__eviksaun_akontese='SIN').
Kampu foun iha futuru: aumenta iha seksaun ne'ebé loos ka kria seksaun foun (haree README iha pakote ne'e).
"""
import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia, TipuKonflitu, TipuRai, EstraguPatrimoniu, NesesidadeUrjente
from .opsaun import STATUS_CHOICES, STATUS_KAZU_CHOICES, STATUS_EDITABLE, DRAFT, ABERTU


class Kazu(models.Model):
	# UUID: bele kria iha HP (offline) la iha risku ID bentrok
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	kode = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name=_("ID Kazu"))
	referensia_rbr = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name=_("Referénsia RbR (Airtable)"))
	titulu = models.CharField(max_length=200, blank=True, verbose_name=_("Naran kazu"))
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT, db_index=True, verbose_name=_("Status Dadus"))
	status_kazu = models.CharField(max_length=15, choices=STATUS_KAZU_CHOICES, default=ABERTU, db_index=True, verbose_name=_("Status Kazu"))

	# Identifikasaun
	data_relatoriu = models.DateField(null=True, blank=True, verbose_name=_("Data simu kazu iha RbR"))
	tinan_simu = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Tinan Simu Kazu iha RbR"))   # automátiku husi data; manuál se data la hatene
	data_akontesimentu = models.DateField(null=True, blank=True, verbose_name=_("Data Akontesimentu"))
	tipu_konflitu = models.ManyToManyField(TipuKonflitu, blank=True, verbose_name=_("Tipu Konflitu Rai"))
	tipu_seluk = models.CharField(max_length=255, blank=True, verbose_name=_("Esplika tipu konflitu \"Seluk\""))
	tinan_disputa_hahu = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Tinan disputa hahú entre parte rua"))
	tipu_rai = models.ForeignKey(TipuRai, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Tipu Rai"))
	deskrisaun = models.TextField(blank=True, verbose_name=_("Observasaun kona-ba tipu kazu"))

	# Fatin administrativu + GPS (uza iha kódigu, filtru, mapa no permisaun → hela iha tabela sentrál)
	munisipiu = models.ForeignKey(Munisipiu, on_delete=models.PROTECT, related_name='kazu_set', verbose_name=_("Munisípiu"))
	postu = models.ForeignKey(PostuAdministrativu, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Postu Administrativu"))
	suku = models.ForeignKey(Suku, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Suku"))
	aldeia = models.ForeignKey(Aldeia, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Aldeia"))
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Latitude"))
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_("Longitude"))
	gps_akurasia = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Akurasia GPS (m)"))
	gps_aproksimadu = models.BooleanField(default=False, verbose_name=_("GPS aproksimadu"))

	# Estragu, urjente, konsentimentu
	estragu = models.ManyToManyField(EstraguPatrimoniu, blank=True, verbose_name=_("Estragu Patrimóniu"))
	estragu_seluk = models.CharField(max_length=255, blank=True, verbose_name=_("Estragu seluk"))
	nesesidade = models.ManyToManyField(NesesidadeUrjente, blank=True, verbose_name=_("Nesesidade Urjente"))
	urjente = models.BooleanField(default=False, db_index=True, verbose_name=_("Urjente"))
	konsentimentu = models.BooleanField(default=False, verbose_name=_("Ema afetada fó konsentimentu informadu ba rekolla no uza dadus"))
	observasaun = models.TextField(blank=True, verbose_name=_("Observasaun Adisionál"))
	la_publika = models.BooleanField(default=False, verbose_name=_("La publika iha portal públiku"))

	# Auditoria
	importasaun = models.ForeignKey('KazuImport', on_delete=models.SET_NULL, null=True, blank=True, related_name='kazu_set', verbose_name=_("Import"))
	created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='kazu_created', verbose_name=_("Investigadór"))
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	synced_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Sinkron iha"))
	verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	verified_at = models.DateTimeField(null=True, blank=True)
	approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	approved_at = models.DateTimeField(null=True, blank=True)
	# Follow-up: Investigadór ne'ebé tenke tuun fali ba terrenu (bele la'ós ida ne'ebé kria kazu)
	followup_ba = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kazu_followup', verbose_name=_("Follow-up ba"))
	followup_at = models.DateTimeField(null=True, blank=True)

	# Rejistu seksaun OneToOne (enxe husi seksaun.py): {relasaun: Model} no {kampu: relasaun}
	SEKSAUN = {}
	KAMPU_SEKSAUN = {}

	class Meta:
		ordering = ['-urjente', '-created_at']
		verbose_name = _("Kazu")
		verbose_name_plural = _("Kazu")
		permissions = [('verify_kazu', 'Bele verifika kazu'), ('approve_kazu', 'Bele aprova kazu')]

	def __str__(self):
		return self.kode or f'{_("Rascunho")} #{str(self.id)[:4].upper()}'

	# ── Seksaun OneToOne ──
	def seksaun(self, rel):
		"""Objetu seksaun (KazuEviksaun, …). La iha seidauk → objetu foun (rai bainhira kazu.save())."""
		cache = self.__dict__.setdefault('_sek_cache', {})
		if rel not in cache:
			model = self.SEKSAUN[rel]
			obj = None
			if not self._state.adding:
				try:
					obj = getattr(self, rel)
				except model.DoesNotExist:
					obj = None
			cache[rel] = obj or model()
		return cache[rel]

	def _marka(self, rel):
		self.__dict__.setdefault('_sek_muda', set()).add(rel)

	def save(self, *args, **kwargs):
		uf = kwargs.get('update_fields')
		if uf is not None:
			uf = list(uf)
			for c in uf:
				if c in self.KAMPU_SEKSAUN:
					self._marka(self.KAMPU_SEKSAUN[c])
			kwargs['update_fields'] = [c for c in uf if c not in self.KAMPU_SEKSAUN]
		super().save(*args, **kwargs)
		for rel in list(self.__dict__.get('_sek_muda', ())):
			obj = self.seksaun(rel)
			obj.kazu = self
			obj.save()
		self.__dict__.pop('_sek_muda', None)

	def refresh_from_db(self, *args, **kwargs):
		self.__dict__.pop('_sek_cache', None)
		self.__dict__.pop('_sek_muda', None)
		return super().refresh_from_db(*args, **kwargs)

	@classmethod
	def kampu(cls, naran):
		"""Field model (Kazu ka seksaun) tuir naran — ba import/export jenériku."""
		if naran in cls.KAMPU_SEKSAUN:
			return cls.SEKSAUN[cls.KAMPU_SEKSAUN[naran]]._meta.get_field(naran)
		return cls._meta.get_field(naran)

	# ── Ajuda ──
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
		from .evidensia import Evidensia
		return self.evidensia.filter(tipu=Evidensia.FOTO).count()

	def video_count(self):
		from .evidensia import Evidensia
		return self.evidensia.filter(tipu=Evidensia.VIDEO).count()


class KazuSequence(models.Model):
	# Kontador ba kódigu kazu: RbR-<MUN>-<TINAN>-<NÚMERU>
	munisipiu = models.ForeignKey(Munisipiu, on_delete=models.CASCADE)
	tinan = models.PositiveSmallIntegerField()
	last = models.PositiveIntegerField(default=0)

	class Meta:
		unique_together = [('munisipiu', 'tinan')]
