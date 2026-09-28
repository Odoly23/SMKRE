from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

TIPU_CHOICES = [
	('KAZU_FOUN', _('Kazu foun')),
	('KAZU_STATUS', _('Status kazu muda')),
	('OFFLINE', _('Autorizasaun offline')),
	('LEGAL', _('Legál (aksaun / prazu)')),
	('SISTEMA', _('Sistema')),
]


class Notification(models.Model):
	recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name=_("Ba"))
	actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name=_("Husi"))
	tipu = models.CharField(max_length=20, choices=TIPU_CHOICES, default='SISTEMA', verbose_name=_("Tipu"))
	message = models.CharField(max_length=255, verbose_name=_("Mensajen"))
	url = models.CharField(max_length=255, blank=True, verbose_name=_("Link"))
	is_urgent = models.BooleanField(default=False, verbose_name=_("Urjente"))
	is_read = models.BooleanField(default=False, verbose_name=_("Lee ona"))
	read_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-is_urgent', '-created_at']
		indexes = [models.Index(fields=['recipient', 'is_read'])]
		verbose_name = _("Notifikasaun")
		verbose_name_plural = _("Notifikasaun")

	def __str__(self):
		return f'{self.recipient} · {self.message}'
