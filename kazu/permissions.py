"""Regra asesu ba kazu ida (haree / edita). Uza iha view, media no API."""
from config.rbac import INVESTIGADOR, ROLE_DASHBOARD
from kazu.models import Kazu, STATUS_EDITABLE
from users.auth_utils import c_user_group


def kazu_queryset(user):
	# Investigadór: kazu rasik deit. Papél seluk (dashboard): kazu hotu.
	group = c_user_group(user)
	qs = Kazu.objects.select_related('munisipiu', 'postu', 'suku', 'aldeia', 'tipu_rai', 'created_by__pesoaluser__pesoal')
	if group == INVESTIGADOR:
		return qs.filter(created_by=user)
	if group in ROLE_DASHBOARD:
		return qs
	return qs.none()


def can_view(user, kazu):
	group = c_user_group(user)
	if group == INVESTIGADOR:
		return kazu.created_by_id == user.id
	return group in ROLE_DASHBOARD


def can_edit(user, kazu):
	# Investigadór nia kazu rasik, status Rascunho / Iha Terrenu / Hein Sinál / Rejeitadu deit
	return (c_user_group(user) == INVESTIGADOR and kazu.created_by_id == user.id
		and kazu.status in STATUS_EDITABLE)
