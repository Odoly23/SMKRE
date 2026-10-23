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
ROLE_LEGAL_EDIT   = [SUPERADMIN, OFISIAL_LEGAL]  # upload dokumentu, nota, haree konfidensiál
ROLE_RELATORIU    = [SUPERADMIN, ADMIN, ANALISTA, OFISIAL_LEGAL]
ROLE_POLICY_KRIA  = [SUPERADMIN, ADMIN, ANALISTA]
ROLE_POLICY_PUBLIKA = [SUPERADMIN, ADMIN]
ROLE_USER_MANAGE  = [SUPERADMIN, ADMIN]
ROLE_OFFLINE_FO   = [SUPERADMIN, ADMIN]       # fó autorizasaun offline (Investigadór + Ofisiál Legál)
ROLE_SEGIMENTU    = [SUPERADMIN, ADMIN, OFISIAL_LEGAL]   # Segimentu kazu: tribunál, notifikasaun, status rezolusaun
ROLE_IMPORT_KAZU  = [ADMIN]                  # Import Excel + hadia lokasaun iha mapa
ROLE_FOLLOWUP     = [SUPERADMIN, ADMIN, OFISIAL_LEGAL]   # Follow-up: haruka kazu fali ba Investigadór (survei foun iha terrenu)
ROLE_POLIGON      = [SUPERADMIN, ADMIN]      # Edita poligon rai kualkér tempu (Investigadór: kazu rasik ne'ebé bele edita)
ROLE_SURVEI_INPUT = [OFISIAL_LEGAL]          # Survei legál (ho autorizasaun input ativu husi Admin)
ROLE_SURVEI_HAREE = [SUPERADMIN, ADMIN, OFISIAL_LEGAL]   # dadus pesoál parte → la ba Analista
ROLE_SURVEI_VERIFIKA = [SUPERADMIN, ADMIN]
ROLE_LEGAL_AUTORIZA = [SUPERADMIN, ADMIN]    # ativa input legál ba Ofisiál Legál (tab iha modulu Legál)
ROLE_INPUT_OFFLINE = [INVESTIGADOR, OFISIAL_LEGAL]       # autorizasaun input / app offline


def roles_admin_can_assign(group):
	# Superadmin bele kria role hotu; Admin bele kria role hotu exeptu superadmin
	if group == SUPERADMIN:
		return ROLE_CHOICES
	if group == ADMIN:
		return [r for r in ROLE_CHOICES if r[0] != SUPERADMIN]
	return []
