import hashlib
import secrets
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


def token_hash(token):
	return hashlib.sha256((token or '').encode()).hexdigest()


class LiveEkran(models.Model):
	# Link privadu ba ekran Live (desktop all-in-one): la presiza login, dadus agregadu no anónimu de'it.
	# Token rai hanesan hash (SHA-256): link kompletu hatudu dala ida de'it bainhira kria.
	naran = models.CharField(max_length=100, verbose_name=_("Naran ekran"))
	token_hash = models.CharField(max_length=64, unique=True, editable=False)
	ativu = models.BooleanField(default=True, verbose_name=_("Ativu"))
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	created_at = models.DateTimeField(auto_now_add=True)
	last_seen = models.DateTimeField(null=True, blank=True, verbose_name=_("Uza ikus"))

	class Meta:
		ordering = ['-created_at']
		verbose_name = _("Ekran Live")
		verbose_name_plural = _("Ekran Live")

	def __str__(self):
		return self.naran

	@classmethod
	def kria(cls, naran, user):
		token = secrets.token_urlsafe(32)
		obj = cls.objects.create(naran=naran, token_hash=token_hash(token), created_by=user)
		return obj, token

	@classmethod
	def husi_token(cls, token):
		return cls.objects.filter(token_hash=token_hash(token), ativu=True).first()
