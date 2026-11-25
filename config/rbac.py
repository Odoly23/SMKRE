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
SEKRETARIADU  = 'sekretariadu'    # Sekretariadu: input kazu + survei legál (online + offline) + aprova (kazu rasik mós)

ROLE_CHOICES = [
	(SUPERADMIN, _('Superadmin')),
	(ADMIN, _('Admin')),
	(SEKRETARIADU, _('Sekretariadu')),
	(ANALISTA, _('Analista')),
	(OFISIAL_LEGAL, _('Ofisiál Legál')),
	(INVESTIGADOR, _('Investigadór')),
]
ROLE_ALL = [r[0] for r in ROLE_CHOICES]

ROLE_DASHBOARD    = [SUPERADMIN, ADMIN, SEKRETARIADU, ANALISTA, OFISIAL_LEGAL]
ROLE_VERIFIKA     = [ADMIN, SEKRETARIADU]    # Verifika (nivel 1): Admin ka Sekretariadu
ROLE_APROVA       = [SUPERADMIN, SEKRETARIADU]   # Aprova (nivel 2): Superadmin ka Sekretariadu (kazu rasik mós)
ROLE_REJEITA      = [SUPERADMIN, ADMIN]      # Rejeita / Kansela (ho razaun)
ROLE_REMATA       = [SUPERADMIN, ADMIN]      # Remata (kompensasaun selu ona)
ROLE_INPUT_KAZU   = [INVESTIGADOR, SEKRETARIADU]   # input kazu (online + app offline)
ROLE_STATUS_KAZU  = [SUPERADMIN, ADMIN, OFISIAL_LEGAL]
ROLE_LEGAL        = [SUPERADMIN, ADMIN, SEKRETARIADU, ANALISTA, OFISIAL_LEGAL]
ROLE_LEGAL_EDIT   = [SUPERADMIN, OFISIAL_LEGAL]  # upload dokumentu, nota, haree konfidensiál
ROLE_RELATORIU    = [SUPERADMIN, ADMIN, SEKRETARIADU, ANALISTA, OFISIAL_LEGAL]
ROLE_POLICY_KRIA  = [SUPERADMIN, ADMIN, ANALISTA]
ROLE_POLICY_PUBLIKA = [SUPERADMIN, ADMIN]
ROLE_USER_MANAGE  = [SUPERADMIN, ADMIN]
ROLE_OFFLINE_FO   = [SUPERADMIN, ADMIN, SEKRETARIADU]   # fó autorizasaun offline (Investigadór + Ofisiál Legál)
ROLE_SEGIMENTU    = [SUPERADMIN, ADMIN, OFISIAL_LEGAL]   # Segimentu kazu: tribunál, notifikasaun, status rezolusaun
ROLE_IMPORT_KAZU  = [ADMIN, SEKRETARIADU]    # Import Excel + hadia lokasaun iha mapa
ROLE_PORTAL       = [SUPERADMIN, ADMIN]      # Konsentimentu + hatudu kazu iha portal públiku
ROLE_DUPLIKADU    = [SUPERADMIN, ADMIN]      # Konfirma "la'ós duplikadu"
ROLE_FOLLOWUP     = [SUPERADMIN, ADMIN, OFISIAL_LEGAL]   # Follow-up: haruka kazu fali ba Investigadór (survei foun iha terrenu)
ROLE_POLIGON      = [SUPERADMIN, ADMIN]      # Edita poligon rai kualkér tempu (Investigadór: kazu rasik ne'ebé bele edita)
ROLE_SURVEI_INPUT = [OFISIAL_LEGAL, SEKRETARIADU]          # Survei legál (ho autorizasaun input ativu husi Admin)
ROLE_SURVEI_HAREE = [SUPERADMIN, ADMIN, SEKRETARIADU, OFISIAL_LEGAL]   # dadus pesoál parte → la ba Analista
ROLE_SURVEI_VERIFIKA = [SUPERADMIN, ADMIN, SEKRETARIADU]
ROLE_LEGAL_AUTORIZA = [SUPERADMIN, ADMIN, SEKRETARIADU]   # ativa input legál ba Ofisiál Legál (tab iha modulu Legál)
ROLE_EXPORT_KOMPLETU = [SUPERADMIN, ADMIN, SEKRETARIADU]   # Excel ho kontaktu pesoál
ROLE_HAMOOS       = [SUPERADMIN]
ROLE_SEM_AUTORIZASAUN = [SEKRETARIADU]       # input kazu / legál (online + offline) la presiza autorizasaun offline
ROLE_EDITA_HOTU   = [SEKRETARIADU]           # edita kazu hotu (kompleta dadus) — exetu kanseladu             # hamoos dadus permanente (utilizador, kazu, survei, dokumentu, publikasaun)
ROLE_INPUT_OFFLINE = [INVESTIGADOR, SEKRETARIADU, OFISIAL_LEGAL]   # autorizasaun input / app offline


# papél (role) ne'ebé grupu ida bele fó: Superadmin → hotu; Admin → hotu exeptu Superadmin
def roles_admin_can_assign(group):
	if group == SUPERADMIN:
		return ROLE_CHOICES
	if group == ADMIN:
		return [r for r in ROLE_CHOICES if r[0] != SUPERADMIN]
	return []
