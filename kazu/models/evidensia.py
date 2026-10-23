"""Evidénsia (foto, vídeo, dokumentu) kazu nian."""
import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


def evidensia_path(instance, filename):
	ext = filename.rsplit('.', 1)[-1].lower()[:5]
	return f'kazu/{instance.kazu_id}/{uuid.uuid4().hex}.{ext}'


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
	kazu = models.ForeignKey('kazu.Kazu', on_delete=models.CASCADE, related_name='evidensia')
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


