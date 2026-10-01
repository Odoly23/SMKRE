from django.conf import settings
from config import rbac
from config.menu import menu_for, bottom_nav_for
from users.auth_utils import c_user_group, c_user_pesoal

# Bandeira kada lian (file SVG lokál iha main/static/main/images/flags/)
LANG_FLAGS = {'tet': 'tl', 'pt': 'pt', 'en': 'gb', 'id': 'id'}


def smkre(request):
	# Variavel ne'ebé template hotu bele uza: group, pesoal, menu, RBAC
	group, pesoal, menu, bnav = None, None, [], []
	if request.user.is_authenticated:
		group = c_user_group(request.user)
		pesoal = c_user_pesoal(request.user)
		menu = menu_for(group)
		if group == rbac.INVESTIGADOR:
			bnav = bottom_nav_for(group)
	return {
		'group': group,
		'role_label': dict(rbac.ROLE_CHOICES).get(group, ''),
		'pesoal': pesoal,
		'menu_items': menu,
		'bottom_nav': bnav,
		'lang_flags': LANG_FLAGS,
		'is_investigador': group == rbac.INVESTIGADOR,
		'can_manage_user': group in rbac.ROLE_USER_MANAGE,
		'can_give_offline': group in rbac.ROLE_OFFLINE_FO,
		'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,            # mapa Leaflet (portal + admin)
	}
