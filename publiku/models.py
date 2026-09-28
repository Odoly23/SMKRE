import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


def publikasaun_path(instance, filename):
	return f'publikasaun/{uuid.uuid4().hex}.pdf'


# ══════════════ PUBLIKASAUN (Policy Brief / relatóriu públiku) ══════════════
# Analista kria (rascunho) → Admin / Superadmin publika → mosu iha portal públiku
class Publikasaun(models.Model):
	RASCUNHO, PUBLIKADU = 'RASCUNHO', 'PUBLIKADU'
	STATUS_CHOICES = [(RASCUNHO, _('Rascunho')), (PUBLIKADU, _('Publikadu'))]
	POLICY, RELATORIU, INFOGRAFIKU = 'POLICY', 'RELATORIU', 'INFOGRAFIKU'
	TIPU_CHOICES = [(POLICY, _('Policy Brief')), (RELATORIU, _('Relatóriu')), (INFOGRAFIKU, _('Infográfiku'))]
	LIAN_CHOICES = [('tet', 'Tetun'), ('pt', 'Português'), ('en', 'English'), ('id', 'Bahasa Indonesia')]

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	tipu = models.CharField(max_length=12, choices=TIPU_CHOICES, default=POLICY, verbose_name=_("Tipu"))
	titulu = models.CharField(max_length=200, verbose_name=_("Títulu"))
	rezumu = models.TextField(max_length=600, verbose_name=_("Rezumu badak"))
	lian = models.CharField(max_length=3, choices=LIAN_CHOICES, default='tet', verbose_name=_("Lian"))
	data = models.DateField(verbose_name=_("Data publikasaun"))
	file = models.FileField(upload_to=publikasaun_path, verbose_name=_("File PDF"))
	tamanu = models.PositiveIntegerField(default=0)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=RASCUNHO, db_index=True, verbose_name=_("Status"))
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	created_at = models.DateTimeField(auto_now_add=True)
	published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	published_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-data', '-created_at']
		verbose_name = _("Publikasaun")
		verbose_name_plural = _("Publikasaun")

	def __str__(self):
		return self.titulu
