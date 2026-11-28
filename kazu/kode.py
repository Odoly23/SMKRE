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


# ── Sujestaun bainhira ID hakerek iha ona (formuláriu + verifikasaun direta) ──
RE_ID_RBR = re.compile(r'^(\s*RBR\s*/\s*)(\d+)(.*)$', re.I)


def numeru_livre():
	"""Númeru kazu tuir mai ne'ebé seidauk uza (referénsia RBR/n, ID RbR-n-…, ID Excel RBR/n_…, kontador)."""
	from kazu.models import Kazu, KazuKontador
	ns = [0]
	for r in Kazu.objects.exclude(referensia_rbr=None).values_list('referensia_rbr', flat=True):
		ns.append(numeru_ref(r) or 0)
	for k in Kazu.objects.exclude(kode=None).values_list('kode', flat=True):
		m = RE_ID_RBR.match(k)
		ns.append(numeru_kode(k) or (int(m[2]) if m else 0))
	kont = KazuKontador.objects.filter(naran='kazu').first()
	ns.append(kont.last if kont else 0)
	return max(ns) + 1


def sujere_id(id_kazu):
	"""ID livre parese ho ID ne'ebé hakerek: RBR/155__ → RBR/<númeru livre>__ ; seluk → <ID>-2, -3…"""
	from kazu.models import Kazu
	iha = lambda v: Kazu.objects.filter(kode__iexact=v).exists()
	n = numeru_livre()
	m = RE_ID_RBR.match(id_kazu or '')
	if m:
		v = f'{m[1].strip()}{n}{m[3]}'
		while iha(v):
			n += 1
			v = f'{m[1].strip()}{n}{m[3]}'
		return v, n
	k = 2
	while iha(f'{id_kazu}-{k}'):
		k += 1
	return f'{id_kazu}-{k}', n
