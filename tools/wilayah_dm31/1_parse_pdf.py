"""Parse Diploma Ministerial 31/2026 (Jornal da República Série I N.º 26 D) → suco/aldeia/posto."""
import json
import re
import sys
import pymupdf

PDF = sys.argv[1]
OUT = sys.argv[2]
ANEXO = ['AIL', 'AIN', 'ATA', 'BAU', 'BOB', 'COV', 'DIL', 'ERM', 'LAU', 'LIQ', 'MAN', 'MNF', 'OEC', 'VIQ']
ROMANO = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV']
HEADER = {'POSTO', 'ADMINISTRATIVO', 'NO', 'ALDEIA', 'OBS'}

doc = pymupdf.open(PDF)
sucos, aldeias, postos = [], [], []
mun = None


def cx(w):
	return (w[0] + w[2]) / 2


def cy(w):
	return (w[1] + w[3]) / 2


def grupu_x(nums):
	# agrupa númeru tuir kolun (x)
	xs = sorted(nums, key=cx)
	gr = []
	for w in xs:
		if gr and cx(w) - cx(gr[-1][-1]) < 22:
			gr[-1].append(w)
		else:
			gr.append([w])
	return gr


for pno in range(doc.page_count):
	page = doc[pno]
	W = [w for w in page.get_text('words') if 46 < w[1] and w[3] < 792]
	txt = ' '.join(w[4] for w in W)
	m = re.search(r'ANEXO\s+([IVX]+)\s*-', txt)
	if m and m.group(1) in ROMANO:
		mun = ANEXO[ROMANO.index(m.group(1))]
	if mun is None:
		continue
	# liña kabeçallu tabela (POSTO ADMINISTRATIVO / NO / SUCO / ALDEIA...)
	hdr = [w for w in W if w[4] == 'ADMINISTRATIVO']
	y_hdr = max(w[3] for w in hdr) + 2 if hdr else 0
	anexo_y = max([w[3] for w in W if w[4].startswith('ANEXO')] or [0])
	W = [w for w in W if w[1] > max(y_hdr, anexo_y + 1)]
	nums = [w for w in W if re.fullmatch(r'\d+', w[4])]
	if not nums:
		continue
	gr = grupu_x(nums)
	g_ald = max(gr, key=len)
	x_ald = sum(cx(w) for w in g_ald) / len(g_ald)
	esq = [g for g in gr if sum(cx(w) for w in g) / len(g) < x_ald - 5]
	dir_ = [g for g in gr if sum(cx(w) for w in g) / len(g) > x_ald + 5]
	g_suco = max(esq, key=len) if esq else []
	# kolun "NO ALDEIA": grupu (los husi aldeia) ne'ebé liña-hanesan ho númeru suco (la'ós digit iha naran aldeia)
	def alinha(g):
		return sum(1 for w in g for n in g_suco_tmp if abs(cy(w) - cy(n)) < 8)
	g_suco_tmp = max(esq, key=len) if esq else []
	dir_ = [g for g in dir_ if sum(cx(w) for w in g) / len(g) > x_ald + 60]
	g_cnt = max(dir_, key=lambda g: (alinha(g), sum(cx(w) for w in g) / len(g))) if dir_ else []
	x_suco = sum(cx(w) for w in g_suco) / len(g_suco) if g_suco else x_ald - 150
	x_cnt = sum(cx(w) for w in g_cnt) / len(g_cnt) if g_cnt else x_ald + 150
	texto = [w for w in W if not re.fullmatch(r'\d+', w[4])]
	# Aldeia
	# kada liafuan iha kolun naran aldeia → númeru aldeia ne'ebé besik liu (y)
	nome_de = {id(n): [] for n in g_ald}
	for w in texto:
		if x_ald + 8 < cx(w) < x_cnt - 12:
			n = min(g_ald, key=lambda n: abs(cy(n) - cy(w)))
			if abs(cy(n) - cy(w)) < 11:
				nome_de[id(n)].append(w)
	for n in g_ald:
		nome = sorted(nome_de[id(n)], key=lambda w: (round(cy(w) / 4), w[0]))
		aldeias.append({'no': int(n[4]), 'name': ' '.join(w[4] for w in nome),
			'mun': mun, 'page': pno + 1, 'y': cy(n)})
	# Suco
	for n in g_suco:
		cand = [w for w in texto if x_suco + 8 < cx(w) < x_ald - 12 and abs(cy(w) - cy(n)) < 16]
		cnt = [w for w in g_cnt if abs(cy(w) - cy(n)) < 8]
		obs = [w for w in texto if cx(w) > x_cnt + 12 and abs(cy(w) - cy(n)) < 16]
		cand.sort(key=lambda w: (round(cy(w)), w[0]))
		sucos.append({'no': int(n[4]), 'name': ' '.join(w[4] for w in cand), 'count': int(cnt[0][4]) if cnt else None,
			'obs': ' '.join(w[4] for w in obs), 'mun': mun, 'page': pno + 1, 'y': cy(n)})
	# Posto (kolun karuk husi NO suco), se iha
	pw = [w for w in texto if cx(w) < x_suco - 15 and w[4] not in HEADER and not w[4].startswith(('Série', 'I,', 'N.°'))]
	linhas = {}
	for w in pw:
		linhas.setdefault(round(cy(w) / 3), []).append(w)
	for k, ws in sorted(linhas.items()):
		postos.append({'name': ' '.join(w[4] for w in sorted(ws, key=lambda w: w[0])), 'mun': mun, 'page': pno + 1, 'y': cy(ws[0])})

json.dump({'sucos': sucos, 'aldeias': aldeias, 'postos': postos}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('sucos', len(sucos), 'aldeias', len(aldeias), 'postos', len(postos))
print('suco no range', min(s['no'] for s in sucos), max(s['no'] for s in sucos))
print('aldeia no range', min(a['no'] for a in aldeias), max(a['no'] for a in aldeias))
print('soma count', sum(s['count'] or 0 for s in sucos), 'sem count', [s['no'] for s in sucos if s['count'] is None][:20])
