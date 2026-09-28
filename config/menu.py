"""
Menu navegasaun tuir papél (RBAC). Fatin IDA deit ba navbar, sidebar no menu okos.
Item ho url_name ne'ebé seidauk iha (faze tuir mai) la mosu automátiku.
"""
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from config import rbac

# (page, url_name, ikon Font Awesome 4.7, label, roles)
MENU = [
	('home', 'home', 'fa-home', _('Varanda'), rbac.ROLE_ALL),
	('kazu', 'kazu-list', 'fa-folder-open', _('Kazu'), rbac.ROLE_ALL),
	('kazu-add', 'kazu-add', 'fa-plus-circle', _('Kazu Foun'), rbac.ROLE_INPUT_KAZU),
	('sinkron', 'sinkron', 'fa-refresh', _('Sinkron'), rbac.ROLE_INPUT_KAZU),
	('dashboard', 'report-dash', 'fa-bar-chart', _('Dashboard'), rbac.ROLE_DASHBOARD),
	('mapa', 'report-mapa', 'fa-map', _('Mapa'), rbac.ROLE_DASHBOARD),
	('relatoriu', 'report-list', 'fa-file-text', _('Relatóriu'), rbac.ROLE_RELATORIU),
	('legal', 'legal-vault', 'fa-balance-scale', _('Legál'), rbac.ROLE_LEGAL),
	('user', 'pesoal-list', 'fa-users', _('Utilizador'), rbac.ROLE_USER_MANAGE),
	('offline', 'offline-list', 'fa-mobile', _('Offline'), rbac.ROLE_USER_MANAGE),
]

# Menu okos (HP) ba Investigadór: maximu 5
BOTTOM_NAV = ['home', 'kazu', 'kazu-add', 'sinkron', 'account']


def menu_for(group):
	items = []
	for page, url_name, icon, label, roles in MENU:
		if group not in roles:
			continue
		try:
			url = reverse(url_name)
		except NoReverseMatch:
			continue
		items.append({'page': page, 'url': url, 'icon': icon, 'label': label})
	return items


def bottom_nav_for(group):
	items = {i['page']: i for i in menu_for(group)}
	items['account'] = {'page': 'account', 'url': reverse('user-account'), 'icon': 'fa-user', 'label': _('Konta')}
	return [items[p] for p in BOTTOM_NAV if p in items]
