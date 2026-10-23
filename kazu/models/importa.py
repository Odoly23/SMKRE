"""Import Excel / Airtable (Admin)."""
import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _



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

