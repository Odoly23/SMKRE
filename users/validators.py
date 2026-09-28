from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class NotDefaultPasswordValidator:
	# Password foun labele hanesan password default
	def validate(self, password, user=None):
		if password == settings.DEFAULT_PASSWORD:
			raise ValidationError(_("Password foun labele hanesan password default."), code='password_default')

	def get_help_text(self):
		return _("Password labele hanesan password default.")
