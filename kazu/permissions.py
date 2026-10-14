"""Regra asesu ba kazu ida (haree / edita). Uza iha view, media no API."""
from django.db.models import Q
from config.rbac import INVESTIGADOR, ROLE_DASHBOARD, ROLE_POLIGON
from kazu.models import Kazu, STATUS_EDITABLE, CANCELED, COMPLETED
from users.auth_utils import c_user_group


def kazu_queryset(user):
	# Investigadór: kazu rasik deit. Papél seluk (dashboard): kazu hotu.
	group = c_user_group(user)
	qs = Kazu.objects.select_related('munisipiu', 'postu', 'suku', 'aldeia', 'tipu_rai', 'created_by__pesoaluser__pesoal')
	if group == INVESTIGADOR:
		return qs.filter(Q(created_by=user) | Q(followup_ba=user))
	if group in ROLE_DASHBOARD:
		return qs
	return qs.none()


def is_responsavel(user, kazu):
	# Investigadór ne'ebé kria kazu ka simu follow-up
	return user.id in (kazu.created_by_id, kazu.followup_ba_id)


def can_view(user, kazu):
	group = c_user_group(user)
	if group == INVESTIGADOR:
		return is_responsavel(user, kazu)
	return group in ROLE_DASHBOARD


def can_edit(user, kazu):
	# Investigadór nia kazu rasik, status Rascunho / Iha Terrenu / Hein Sinál / Rejeitadu deit
	return (c_user_group(user) == INVESTIGADOR and is_responsavel(user, kazu)
		and kazu.status in STATUS_EDITABLE)


def can_poligon(user, kazu):
	# Poligon rai: Investigadór (hanesan can_edit) · Admin / Superadmin kualkér tempu exeptu Kanseladu / Remata
	if c_user_group(user) in ROLE_POLIGON:
		return kazu.status not in (CANCELED, COMPLETED)
	return can_edit(user, kazu)
