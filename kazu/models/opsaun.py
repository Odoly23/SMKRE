"""Opsaun (choices) no status kazu — fatin IDA ba konstante sira."""
from django.utils.translation import gettext_lazy as _

# ══════════════ STATUS ══════════════
# Status Dadus (fluxu dadus: HP → server → verifikasaun)
DRAFT, ONGOING, PENDING = 'DRAFT', 'ONGOING', 'PENDING'
SYNCED, VERIFIED, APPROVED, COMPLETED = 'SYNCED', 'VERIFIED', 'APPROVED', 'COMPLETED'
REJECTED, CANCELED = 'REJECTED', 'CANCELED'
FOLLOWUP = 'FOLLOWUP'                                     # tuun fali ba terrenu (survei foun)

STATUS_CHOICES = [
	(DRAFT, _('Rascunho')),
	(ONGOING, _('Iha Terrenu')),
	(PENDING, _('Hein Sinál')),
	(SYNCED, _('Hein Verifikasaun')),
	(VERIFIED, _('Verifikadu')),
	(APPROVED, _('Aprovadu')),
	(COMPLETED, _('Remata')),
	(REJECTED, _('Rejeitadu')),
	(FOLLOWUP, _('Follow-up')),
	(CANCELED, _('Kanseladu')),
]
# Opsaun husi formuláriu baze dadus sentrál RbR (Airtable) — Sin / Lae / La hatene
SIN, LAE, LAHATENE = 'SIN', 'LAE', 'LAHATENE'
SIN_LAE_CHOICES = [(SIN, _('Sin')), (LAE, _('Lae')), (LAHATENE, _('La hatene'))]

ENTIDADE_CHOICES = [
	('AJENSIA_AUTONOMU', _('Ajénsia Autónomu')), ('CCLN_VETERANU', _('CCLN-Veteranu')),
	('EMPREZA_PUBLIKU', _('Empreza Públiku')), ('GOVERNU', _('Governu')),
	('KOMPANIA_INTERNASIONAL', _('Kompañia Internasionál')), ('KOMPANIA_NASIONAL', _('Kompañia Nasionál')),
	('KONVENSAUN_RELIJIOZU', _('Konvensaun Relijiozu')), ('PARTIDU_POLITIKU', _('Partidu Polítiku')),
	('PNTL_FFDTL', _('PNTL / F-FDTL')), ('SELUK', _('Seluk')), ('LAHATENE', _('La hatene')),
]
RAI_UNIDADE_CHOICES = [('M2', _('Metru kuadradu (m²)')), ('HA', _('Hektar (ha)'))]

STATUS_EDITABLE = [DRAFT, ONGOING, PENDING, REJECTED, FOLLOWUP]     # Investigadór bele edita
STATUS_SUBMITTED = [SYNCED, VERIFIED, APPROVED, COMPLETED]

# Status Kazu (prosesu kazu — Anexu A)
ABERTU, INVESTIGASAUN, AKSAUN_LEGAL, TAKA = 'ABERTU', 'INVESTIGASAUN', 'AKSAUN_LEGAL', 'TAKA'
STATUS_KAZU_CHOICES = [
	(ABERTU, _('Abertu')),
	(INVESTIGASAUN, _('Investigasaun')),
	(AKSAUN_LEGAL, _('Aksaun Legál')),
	(TAKA, _('Taka')),
]
# Desizaun RbR ba kazu (troka Status Kazu iha ekran hotu; Status Kazu tuan rai iha DB de'it)
ARKIVU, MONITORIZASAUN, ADVOKASIA = 'ARKIVU', 'MONITORIZASAUN', 'ADVOKASIA'
DESIZAUN_RBR_CHOICES = [(ARKIVU, _('Arkivu')), (MONITORIZASAUN, _('Monitorizasaun')), (ADVOKASIA, _('Advokasia ativu'))]
DESIZAUN_AJUDA = {
	ARKIVU: _('Kazu rezolve ona ka RbR refere ona ba advogadu privadu.'),
}
# Migrasaun Status Kazu tuan → Desizaun RbR
STATUS_KAZU_BA_DESIZAUN = {AKSAUN_LEGAL: ADVOKASIA, TAKA: ARKIVU, ABERTU: MONITORIZASAUN, INVESTIGASAUN: MONITORIZASAUN}

