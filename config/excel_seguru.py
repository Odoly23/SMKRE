"""Proteje kontra Formula/CSV Injection (CWE-1236) iha file Excel/CSV ne'ebé eksporta.

Dadus husi utilizador (titulu, deskrisaun, naran…) ne'ebé hahú ho '=', '+', '-', '@',
TAB ka CR bele sai fórmula bainhira ema loke iha Excel/LibreOffice (ex. =HYPERLINK(...) atu
hafasik dadus, ka komandu sistema). Prefix ho apóstrofu ('): Excel trata hanesan testu.

Númeru simples no koordenada GPS (ex. "-8.6121, 125.5") hahú ho '-' maibé la'ós fórmula
perigozu — la prefix, atu eksporta → import fali (round-trip) la estraga. Payload fórmula
iha letra/parénteses/pipe → prefix nafatin.
"""
import re

GATILLU = ('=', '+', '-', '@', '\t', '\r', '\n', '|', '\x00')
# Númeru, pursentu, koordenada GPS: dígitu, ponto, vírgula, espasu, sinál — seguru, la prefix
_NUMERIKU = re.compile(r'^[-+]?[\d.,%\s-]+$')


def seguru(valor):
	if isinstance(valor, str) and valor[:1] in GATILLU and not _NUMERIKU.match(valor):
		return "'" + valor
	return valor


def lina_seguru(lina):
	return [seguru(v) for v in lina]
