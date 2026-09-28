from django import template
from config.rbac import ROLE_CHOICES
from users.auth_utils import c_user_group

register = template.Library()
ROLE_LABEL = dict(ROLE_CHOICES)


@register.filter
def role_of(user):
	# {{ user|role_of }} → naran papél (label)
	return ROLE_LABEL.get(c_user_group(user), '-')


@register.filter
def role_code(user):
	return c_user_group(user) or ''
