"""Formatu ID Kazu SIBAR: RbR-<númeru>-<Munisípiu>-<Postu>-<Suku>-<Aldeia>
Ezemplu: RbR-01-Dili-Dom Aleixo-Fatuhada-Bairo Pite
- númeru: kontador global RbR (la repete, la reinisia kada tinan/munisípiu);
  kazu ho "Numeru kazu" RBR/153 → uza 153 (hanesan pasta fíziku RBR-153)
- fatin ne'ebé mamuk (ex. aldeia) la tama
Funsaun puru (la iha query) — uza iha kazu.services no migrasaun 0021."""
import re

KODE_MAX = 120
RE_REF = re.compile(r'^\s*RBR\s*/\s*(\d+)\s*$', re.I)       # referénsia RBR/153
RE_KODE = re.compile(r'^RbR-(\d+)-', re.I)                   # ID formatu foun RbR-153-…
RE_KODE_TUAN = r'^RbR-[A-Z]{3}-[0-9]{4}-[0-9]{4,}$'          # ID tuan RbR-LIQ-2026-0001 (regex query)


def numeru_ref(ref):
	m = RE_REF.match(ref or '')
	return int(m[1]) if m else None


def numeru_kode(kode):
	m = RE_KODE.match(kode or '')
	return int(m[1]) if m else None


def prefiksu(n):
	return f'RbR-{n:02d}-'


def formatu(n, *fatin):
	parte = ['RbR', f'{n:02d}'] + [' '.join(str(x).split()) for x in fatin if x and str(x).strip()]
	return '-'.join(parte)[:KODE_MAX]


# númeru boot liu ne'ebé uza ona (referénsia RBR/n + ID formatu foun) → kontador hahú husi ne'e
def numeru_maks(referensia, kodes):
	ns = [numeru_ref(r) for r in referensia] + [numeru_kode(k) for k in kodes]
	return max([n for n in ns if n] or [0])
