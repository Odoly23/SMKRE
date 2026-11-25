from users.models import Pesoal, OfflinePermission


def c_user_pesoal(user):
	objects = Pesoal.objects.filter(pesoaluser__user=user).select_related('munisipiu', 'pos').first()
	obj = ""
	if objects: obj = objects
	return obj


def c_user_group(user):
	# Seguru: retorna None se utilizador seidauk login ka la iha group (la iha IndexError)
	if not user or not user.is_authenticated:
		return None
	cache = getattr(user, '_smkre_group', False)
	if cache is not False:
		return cache
	group = user.groups.values_list('name', flat=True).first()
	user._smkre_group = group
	return group


def c_user_offline(user):
	# Autorizasaun offline ne'ebé validu agora (ka None)
	return OfflinePermission.objects.valid().filter(user=user).order_by('-end_date').first()


# papél ne'ebé la presiza autorizasaun offline (Sekretariadu): input kazu / legál bainhira de'it
def sem_autorizasaun(user):
	from config.rbac import ROLE_SEM_AUTORIZASAUN
	return c_user_group(user) in ROLE_SEM_AUTORIZASAUN


# munisípiu ne'ebé utilizador bele input kazu:
#   [] = munisípiu HOTU (Sekretariadu, la presiza hili knaar) · lista = knaar Investigadór (1–2) · None = seidauk iha knaar
def munisipiu_input(user):
	from config.rbac import SEKRETARIADU
	if c_user_group(user) == SEKRETARIADU:
		return []
	pesoal = c_user_pesoal(user)
	if not pesoal or not pesoal.munisipiu:
		return None
	return pesoal.munisipiu_lista
