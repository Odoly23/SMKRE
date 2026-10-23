"""
Menu navegasaun tuir papél (RBAC). Fatin IDA deit ba navbar (dropdown), sidebar HP no menu okos.
Item ho url_name ne'ebé seidauk iha la mosu automátiku. Grupu ho item ida de'it → link simples.
"""
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from config import rbac

# Grupu: (xave, ikon, label, [ (page, url_name, ikon, label, roles[, opsaun]) ])
MENU = [
	('home', 'fa-home', _('Varanda'), [
		('home', 'home', 'fa-home', _('Varanda'), rbac.ROLE_ALL),
	]),
	('kazu', 'fa-folder-open', _('Kazu'), [
		('kazu', 'kazu-list', 'fa-list', _('Lista Kazu'), rbac.ROLE_ALL),
		('kazu-add', 'kazu-add', 'fa-plus-circle', _('Kazu Foun'), rbac.ROLE_INPUT_KAZU),
		('sinkron', 'sinkron', 'fa-mobile', _('App Offline'), rbac.ROLE_INPUT_OFFLINE),
		('import', 'kazu-import', 'fa-upload', _('Import'), rbac.ROLE_IMPORT_KAZU),
	]),
	('legal', 'fa-balance-scale', _('Legál'), [
		('legal', 'legal-dash', 'fa-tachometer', _('Dashboard Legál'), rbac.ROLE_LEGAL),
		('legal-kazu', 'legal-kazu-list', 'fa-balance-scale', _('Kazu Legál'), rbac.ROLE_LEGAL),
		('legal-survei', 'legal-survei-list', 'fa-clipboard', _('Survei Legál'), rbac.ROLE_SURVEI_HAREE),
		('legal-input', 'legal-survei-add', 'fa-pencil-square-o', _('Input Legál'), rbac.ROLE_SURVEI_INPUT, {'autorizasaun': True}),
		('legal-autoriza', 'legal-autorizasaun', 'fa-unlock-alt', _('Ativa Input Legál'), rbac.ROLE_LEGAL_AUTORIZA),
		('legal-vault', 'legal-vault', 'fa-archive', _('Document Vault'), rbac.ROLE_LEGAL),
	]),
	('relatoriu', 'fa-bar-chart', _('Relatóriu'), [
		('dashboard', 'report-dash', 'fa-bar-chart', _('Dashboard'), rbac.ROLE_DASHBOARD),
		('live', 'report-live', 'fa-television', _('Live'), rbac.ROLE_DASHBOARD, {'tab_foun': True}),
		('mapa', 'report-mapa', 'fa-map', _('Mapa'), rbac.ROLE_DASHBOARD),
		('grafiku', 'report-chart', 'fa-line-chart', _('Gráfiku'), rbac.ROLE_DASHBOARD),
		('relatoriu', 'report-list', 'fa-file-text', _('Lista Relatóriu'), rbac.ROLE_RELATORIU),
		('publikasaun', 'publikasaun-list', 'fa-newspaper-o', _('Publikasaun'), rbac.ROLE_POLICY_KRIA),
	]),
	('admin', 'fa-cogs', _('Administrasaun'), [
		('user', 'pesoal-list', 'fa-users', _('Utilizador'), rbac.ROLE_USER_MANAGE),
		('offline', 'offline-list', 'fa-mobile', _('Autorizasaun Offline'), rbac.ROLE_USER_MANAGE),
		('live-ekran', 'report-live-ekran', 'fa-link', _('Ekran Live'), rbac.ROLE_USER_MANAGE),
	]),
]

# Menu okos (HP) ba Investigadór: maximu 5
BOTTOM_NAV = ['home', 'kazu', 'kazu-add', 'sinkron', 'account']


def _items(group, user, entries):
	items, ativu = [], None
	for e in entries:
		page, url_name, icon, label, roles = e[:5]
		opt = e[5] if len(e) > 5 else {}
		if group not in roles:
			continue
		if opt.get('autorizasaun'):                 # Input Legál: autorizasaun ativu husi Admin de'it
			if ativu is None:
				from legal.survei import input_ativu
				ativu = bool(user) and input_ativu(user)
			if not ativu:
				continue
		try:
			url = reverse(url_name)
		except NoReverseMatch:
			continue
		items.append({'page': page, 'url': url, 'icon': icon, 'label': label, 'tab_foun': opt.get('tab_foun', False)})
	return items


def menu_grupu_for(group, user=None):
	grupu = []
	for key, icon, label, entries in MENU:
		items = _items(group, user, entries)
		if items:
			grupu.append({'key': key, 'icon': icon, 'label': label, 'items': items, 'pages': [i['page'] for i in items],
				'simples': len(items) == 1})
	return grupu


def menu_for(group, user=None):
	# Lista simples (menu okos HP)
	return [i for g in menu_grupu_for(group, user) for i in g['items']]


def bottom_nav_for(group, user=None):
	items = {i['page']: i for i in menu_for(group, user)}
	items['account'] = {'page': 'account', 'url': reverse('user-account'), 'icon': 'fa-user', 'label': _('Konta')}
	return [items[p] for p in BOTTOM_NAV if p in items]
