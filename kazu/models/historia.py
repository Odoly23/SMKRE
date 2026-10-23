"""Istória kazu: se, bainhira, razaun."""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from .opsaun import STATUS_CHOICES, STATUS_KAZU_CHOICES


# ══════════════ ISTÓRIA (se, bainhira, razaun) ══════════════
class KazuHistoria(models.Model):
	DADUS, KAZU, EDITA, LEE = 'DADUS', 'KAZU', 'EDITA', 'LEE'
	TIPU_CHOICES = [(DADUS, _('Status Dadus')), (KAZU, _('Status Kazu')), (EDITA, _('Edita')), (LEE, _('Lee'))]
	kazu = models.ForeignKey('kazu.Kazu', on_delete=models.CASCADE, related_name='historia')
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
