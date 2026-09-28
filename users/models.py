import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from custom.models import Pozisaun, Munisipiu

SEXO_CHOICES = [('Mane', _('Mane')), ('Feto', _('Feto'))]


def pesoal_foto_path(instance, filename):
	ext = filename.rsplit('.', 1)[-1].lower()
	return f'pesoal/{instance.uuid}/foto.{ext}'


class Pesoal(models.Model):
	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)   # uza iha URL (la'ós id)
	name = models.CharField(max_length=100, null=True, blank=False, verbose_name=_("Naran"))
	sexo = models.CharField(choices=SEXO_CHOICES, max_length=4, null=True, blank=False, verbose_name=_("Sexu"))
	pos = models.ForeignKey(Pozisaun, on_delete=models.SET_NULL, null=True, blank=True, related_name="pesoal", verbose_name=_("Pozisaun"))
	phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Nu. Telf."))
	email = models.EmailField(unique=True, null=True, blank=False, verbose_name=_("Email"))
	munisipiu = models.ForeignKey(Munisipiu, on_delete=models.SET_NULL, null=True, blank=True, related_name="pesoal", verbose_name=_("Munisípiu Knaar"))
	image = models.ImageField(upload_to=pesoal_foto_path, null=True, blank=True, verbose_name=_("Foto"))
	lian = models.CharField(max_length=5, choices=settings.LANGUAGES, default='tet', verbose_name=_("Lian"))
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']
		verbose_name = _("Pesoal")
		verbose_name_plural = _("Pesoal")

	def __str__(self):
		return self.name or self.email or '-'

	@property
	def inisial(self):
		parts = (self.name or '?').split()
		return ''.join(p[0] for p in parts[:2]).upper()


class PesoalUser(models.Model):
	pesoal = models.OneToOneField(Pesoal, on_delete=models.CASCADE, null=True, related_name="pesoaluser")
	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
	must_change_password = models.BooleanField(default=True, verbose_name=_("Tenke troka password"))

	class Meta:
		verbose_name = _("Konta Pesoal")
		verbose_name_plural = _("Konta Pesoal")

	def __str__(self):
		template = '{0.pesoal} - {0.user}'
		return template.format(self)


class OfflinePermissionQuerySet(models.QuerySet):
	def valid(self):
		return self.filter(is_active=True, end_date__gt=timezone.now())


class OfflinePermission(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offline_permission", verbose_name=_("Investigadór"))
	given_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="offline_given", verbose_name=_("Fó husi"))
	start_date = models.DateTimeField(default=timezone.now, verbose_name=_("Data hahú"))
	end_date = models.DateTimeField(verbose_name=_("Data remata"))
	is_active = models.BooleanField(default=True, verbose_name=_("Ativu"))
	cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="offline_cancelled")
	cancelled_at = models.DateTimeField(null=True, blank=True)
	note = models.CharField(max_length=255, blank=True, verbose_name=_("Nota"))

	objects = OfflinePermissionQuerySet.as_manager()

	class Meta:
		ordering = ['-start_date']
		verbose_name = _("Autorizasaun Offline")
		verbose_name_plural = _("Autorizasaun Offline")

	def __str__(self):
		return f'{self.user} · {self.end_date:%d/%m/%Y}'

	def save(self, *args, **kwargs):
		if not self.end_date:
			self.end_date = self.start_date + timedelta(days=settings.OFFLINE_PERMISSION_DAYS)
		super().save(*args, **kwargs)

	@property
	def is_valid(self):
		return self.is_active and self.end_date > timezone.now()

	@property
	def days_left(self):
		if not self.is_valid:
			return 0
		return max(0, (self.end_date - timezone.now()).days)
