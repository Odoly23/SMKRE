"""
RBAC — Role-Based Access Control
Regra asesu HOTU iha fatin ida ne'e. Atu muda asesu, muda lista iha okos deit.
Naran role = naran Group iha Django.
"""
from django.utils.translation import gettext_lazy as _

SUPERADMIN    = 'superadmin'
ADMIN         = 'admin'
ANALISTA      = 'analista'        # Advocacy Coordinator
OFISIAL_LEGAL = 'ofisial_legal'   # Legal Advisor
INVESTIGADOR  = 'investigador'    # Staff terrenu

ROLE_CHOICES = [
	(SUPERADMIN, _('Superadmin')),
	(ADMIN, _('Admin')),
	(ANALISTA, _('Analista')),
	(OFISIAL_LEGAL, _('Ofisiál Legál')),
	(INVESTIGADOR, _('Investigadór')),
]
ROLE_ALL = [r[0] for r in ROLE_CHOICES]

ROLE_DASHBOARD    = [SUPERADMIN, ADMIN, ANALISTA, OFISIAL_LEGAL]
ROLE_VERIFIKA     = [ADMIN]                  # Admin: Verifika (nivel 1)
ROLE_APROVA       = [SUPERADMIN]             # Superadmin: Aprova (nivel 2)
ROLE_REJEITA      = [SUPERADMIN, ADMIN]      # Rejeita / Kansela (ho razaun)
ROLE_REMATA       = [SUPERADMIN, ADMIN]      # Remata (kompensasaun selu ona)
ROLE_INPUT_KAZU   = [INVESTIGADOR]
ROLE_STATUS_KAZU  = [SUPERADMIN, ADMIN, OFISIAL_LEGAL]
ROLE_LEGAL        = [SUPERADMIN, ADMIN, ANALISTA, OFISIAL_LEGAL]
ROLE_LEGAL_EDIT   = [OFISIAL_LEGAL]
ROLE_RELATORIU    = [SUPERADMIN, ADMIN, ANALISTA, OFISIAL_LEGAL]
ROLE_POLICY_KRIA  = [SUPERADMIN, ADMIN, ANALISTA]
ROLE_POLICY_PUBLIKA = [SUPERADMIN, ADMIN]
ROLE_USER_MANAGE  = [SUPERADMIN, ADMIN]
ROLE_OFFLINE_FO   = [ADMIN]


def roles_admin_can_assign(group):
	# Superadmin bele kria role hotu; Admin bele kria role hotu exeptu superadmin
	if group == SUPERADMIN:
		return ROLE_CHOICES
	if group == ADMIN:
		return [r for r in ROLE_CHOICES if r[0] != SUPERADMIN]
	return []
