from django import template
from django.utils.html import escape, escapejs
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


@register.filter
def js_html(value):
	# Testu ba laran string JS ne'ebé sei sai HTML (popup mapa): escape HTML uluk, depois escape JS (anti-XSS)
	return escapejs(escape('' if value is None else value))


@register.simple_tag(takes_context=True)
def url_pajina(context, n):
	# Link ba pájina n ne'ebé rai filtru hotu (q, status, munisípiu...) husi URL atuál
	q = context['request'].GET.copy()
	q['page'] = n
	return '?' + q.urlencode()


@register.filter
def numeru(pajina, forloop_counter0):
	# Númeru kontinua entre pájina: pájina 2 hahú iha 11
	try:
		return pajina.start_index() + forloop_counter0
	except AttributeError:
		return forloop_counter0 + 1
