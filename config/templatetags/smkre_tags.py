from django import template
from django.utils.html import escape, escapejs
from config.rbac import ROLE_CHOICES
from users.auth_utils import c_user_group

register = template.Library()
ROLE_LABEL = dict(ROLE_CHOICES)


# {{ user|role_of }} → naran papél (label) husi utilizador
@register.filter
def role_of(user):
	return ROLE_LABEL.get(c_user_group(user), '-')


# {{ user|role_code }} → kódigu papél (role) husi utilizador
@register.filter
def role_code(user):
	return c_user_group(user) or ''


# testu ba laran string JS ne'ebé sei sai HTML (popup mapa): escape HTML uluk, depois escape JS (anti-XSS)
@register.filter
def js_html(value):
	return escapejs(escape('' if value is None else value))


# link ba pájina n ne'ebé rai filtru hotu (q, status, munisípiu...) husi URL atuál
@register.simple_tag(takes_context=True)
def url_pajina(context, n):
	q = context['request'].GET.copy()
	q['page'] = n
	return '?' + q.urlencode()


# númeru kontinua entre pájina: pájina 2 hahú iha 11 (foun liu = númeru 1)
@register.filter
def numeru(pajina, forloop_counter0):
	try:
		return pajina.start_index() + forloop_counter0
	except AttributeError:
		return forloop_counter0 + 1
