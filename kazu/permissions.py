"""Regra asesu ba kazu ida (haree / edita). Uza iha view, media no API."""
from django.db.models import Q
from config.rbac import INVESTIGADOR, ROLE_DASHBOARD, ROLE_POLIGON, ROLE_INPUT_KAZU, ROLE_EDITA_HOTU
from kazu.models import Kazu, STATUS_EDITABLE, CANCELED, COMPLETED
from users.auth_utils import c_user_group


# queryset kazu tuir papél: Investigadór → kazu rasik de'it; papél dashboard → kazu hotu
def kazu_queryset(user):
	group = c_user_group(user)
	qs = Kazu.objects.select_related('munisipiu', 'postu', 'suku', 'aldeia', 'tipu_rai', 'created_by__pesoaluser__pesoal')
	if group == INVESTIGADOR:
		return qs.filter(Q(created_by=user) | Q(followup_ba=user))
	if group in ROLE_DASHBOARD:
		return qs
	return qs.none()


# Investigadór ne'ebé responsavel ba kazu: nia mak kria ka simu follow-up
def is_responsavel(user, kazu):
	return user.id in (kazu.created_by_id, kazu.followup_ba_id)


# bele haree kazu? Investigadór → responsavel de'it; papél seluk → papél dashboard
def can_view(user, kazu):
	group = c_user_group(user)
	if group == INVESTIGADOR:
		return is_responsavel(user, kazu)
	return group in ROLE_DASHBOARD


# bele edita kazu? Investigadór / Sekretariadu: kazu rasik, status Rascunho / Iha Terrenu / Hein Sinál / Rejeitadu de'it
def can_edit(user, kazu):
	if c_user_group(user) in ROLE_EDITA_HOTU:          # Sekretariadu: kompleta dadus kazu hotu (exetu kanseladu)
		return kazu.status != CANCELED
	return (c_user_group(user) in ROLE_INPUT_KAZU and is_responsavel(user, kazu)
		and kazu.status in STATUS_EDITABLE)


# bele dezeña poligon rai? Investigadór (hanesan can_edit); Admin/Superadmin kualkér tempu exeptu Kanseladu/Remata
def can_poligon(user, kazu):
	if c_user_group(user) in ROLE_POLIGON:
		return kazu.status not in (CANCELED, COMPLETED)
	return can_edit(user, kazu)
