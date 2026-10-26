"""Model kazu — fahe ba file ki'ik tuir seksaun (fásil atu manutensaun).

    opsaun.py     status no choices (konstante hotu)
    kazu.py       Kazu (tabela sentrál) + KazuSequence (kódigu)
    seksaun.py    seksaun OneToOne: KazuFatin, KazuEntidade, KazuPopulasaun, KazuEviksaun, KazuPortavos
    afetadu.py    UmaKainAfetada, InsidenteEviksaun, AtorEnvolvidu (lista laran)
    evidensia.py  Evidensia (foto, vídeo, dokumentu)
    segimentu.py  KazuSegimentu, KazuAkompanamentu (eskritóriu RbR)
    importa.py    KazuImport (Excel / Airtable)
    historia.py   KazuHistoria (auditoria)

Import hanesan uluk: `from kazu.models import Kazu, VERIFIED, KazuEviksaun`.
"""
from .opsaun import *                                    # noqa: F401,F403
from .opsaun import (DRAFT, ONGOING, PENDING, SYNCED, VERIFIED, APPROVED, COMPLETED, REJECTED, CANCELED, FOLLOWUP,
	STATUS_CHOICES, SIN, LAE, LAHATENE, SIN_LAE_CHOICES, ENTIDADE_CHOICES, RAI_UNIDADE_CHOICES, STATUS_EDITABLE,
	STATUS_SUBMITTED, ABERTU, INVESTIGASAUN, AKSAUN_LEGAL, TAKA, STATUS_KAZU_CHOICES,
	ARKIVU, MONITORIZASAUN, ADVOKASIA, DESIZAUN_RBR_CHOICES, DESIZAUN_AJUDA)
from .kazu import Kazu, KazuSequence
from .seksaun import KazuFatin, KazuEntidade, KazuPopulasaun, KazuEviksaun, KazuPortavos, SEKSAUN, SEKSAUN_REL
from .afetadu import UmaKainAfetada, InsidenteEviksaun, AtorEnvolvidu
from .evidensia import Evidensia, evidensia_path
from .segimentu import KazuSegimentu, KazuAkompanamentu
from .importa import KazuImport
from .historia import KazuHistoria

__all__ = [
	'Kazu', 'KazuSequence', 'KazuFatin', 'KazuEntidade', 'KazuPopulasaun', 'KazuEviksaun', 'KazuPortavos', 'SEKSAUN', 'SEKSAUN_REL',
	'UmaKainAfetada', 'InsidenteEviksaun', 'AtorEnvolvidu', 'Evidensia', 'evidensia_path', 'KazuSegimentu', 'KazuAkompanamentu',
	'KazuImport', 'KazuHistoria',
	'DRAFT', 'ONGOING', 'PENDING', 'SYNCED', 'VERIFIED', 'APPROVED', 'COMPLETED', 'REJECTED', 'CANCELED', 'FOLLOWUP',
	'STATUS_CHOICES', 'SIN', 'LAE', 'LAHATENE', 'SIN_LAE_CHOICES', 'ENTIDADE_CHOICES', 'RAI_UNIDADE_CHOICES',
	'STATUS_EDITABLE', 'STATUS_SUBMITTED', 'ABERTU', 'INVESTIGASAUN', 'AKSAUN_LEGAL', 'TAKA', 'STATUS_KAZU_CHOICES',
	'ARKIVU', 'MONITORIZASAUN', 'ADVOKASIA', 'DESIZAUN_RBR_CHOICES', 'DESIZAUN_AJUDA',
]
