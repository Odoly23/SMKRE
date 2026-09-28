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
