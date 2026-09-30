"""Aldeia→Suco (kolun NO ALDEIA) no Suco→Posto (label iha klaran bloku, DP)."""
import json
import sys
from collections import defaultdict

J = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
# Orden tuir pozisaun iha dokumentu (página, liña) — PDF iha salah-ketik númeru (ex. 354 ba 344)
sucos = sorted(J['sucos'], key=lambda s: (s['page'], s['y']))
aldeias = sorted(J['aldeias'], key=lambda a: (a['page'], a['y']))
for i, s in enumerate(sucos, start=1):
	s['no_pdf'], s['no'] = s['no'], i
for i, a in enumerate(aldeias, start=1):
	a['no_pdf'], a['no'] = a['no'], i
print('Númeru suco PDF salah:', [(s['no'], s['no_pdf'], s['name']) for s in sucos if s['no'] != s['no_pdf']])
print('Númeru aldeia PDF salah:', [(a['no'], a['no_pdf'], a['name']) for a in aldeias if a['no'] != a['no_pdf']][:20])
labels = J['postos']

# ── 2. Koordenada kontínua kada ANEXO (pt), husi liña aldeia ──
rows_pg = defaultdict(list)
for a in aldeias:
	rows_pg[a['page']].append(a['y'])
TOP, BOT = {}, {}
for pg, ys in rows_pg.items():
	ys = sorted(ys)
	h = min(b - a for a, b in zip(ys, ys[1:])) if len(ys) > 1 else 20
	TOP[pg], BOT[pg] = ys[0] - h / 2, ys[-1] + h / 2
ordem = {}
for mun in dict.fromkeys(s['mun'] for s in sucos):
	acc = 0
	for pg in sorted({a['page'] for a in aldeias if a['mun'] == mun}):
		ordem[pg] = acc
		acc += BOT[pg] - TOP[pg]


ROWS = defaultdict(list)
for a in aldeias:
	ROWS[a['page']].append(a['y'])
for pg in ROWS:
	ROWS[pg].sort()
ORD = {}
for mun in dict.fromkeys(s['mun'] for s in sucos):
	acc = 0
	for pg in sorted({a['page'] for a in aldeias if a['mun'] == mun}):
		ORD[pg] = acc
		acc += len(ROWS[pg])


def pos(pg, y):
	# pozisaun iha unidade "liña aldeia" (0.5 = klaran liña primeiru)
	ys = ROWS[pg]
	if y <= ys[0]:
		h = (ys[1] - ys[0]) if len(ys) > 1 else 20
		return ORD[pg] + 0.5 + (y - ys[0]) / h
	if y >= ys[-1]:
		h = (ys[-1] - ys[-2]) if len(ys) > 1 else 20
		return ORD[pg] + len(ys) - 0.5 + (y - ys[-1]) / h
	for i in range(len(ys) - 1):
		if ys[i] <= y <= ys[i + 1]:
			return ORD[pg] + i + 0.5 + (y - ys[i]) / (ys[i + 1] - ys[i])


# ── 1. Aldeia → Suco: DP (suco iha klaran nia bloku) + kolun ofisiál "NO ALDEIA" ──
MAXB = 30
for mun in dict.fromkeys(x['mun'] for x in sucos):
	ss = [x for x in sucos if x['mun'] == mun]
	aa = [x for x in aldeias if x['mun'] == mun]
	P = [pos(x['page'], x['y']) for x in aa]
	cs = [pos(x['page'], x['y']) for x in ss]
	n, m = len(ss), len(aa)
	INF = float('inf')
	dp = [[INF] * (m + 1) for _ in range(n + 1)]
	bk = [[0] * (m + 1) for _ in range(n + 1)]
	dp[0][0] = 0
	for j in range(1, n + 1):
		cnt = ss[j - 1]['count']
		for i in range(j, m + 1):
			for k in range(max(j - 1, i - MAXB), i):
				if dp[j - 1][k] == INF:
					continue
				centro = (P[k] + P[i - 1]) / 2
				custo = abs(centro - cs[j - 1]) + (0 if cnt is None or cnt == i - k else 400)
				if dp[j - 1][k] + custo < dp[j][i]:
					dp[j][i], bk[j][i] = dp[j - 1][k] + custo, k
	i = m
	for j in range(n, 0, -1):
		k = bk[j][i]
		for x in aa[k:i]:
			x['suco'] = ss[j - 1]['no']
		ss[j - 1]['n_ald'] = i - k
		i = k
dif = [(x['no'], x['name'], x['count'], x['n_ald']) for x in sucos if x['count'] is not None and x['count'] != x['n_ald']]
print('NO ALDEIA PDF ≠ liña tabela:', dif)
print('NO ALDEIA mamuk iha PDF (uza liña):', [(x['no'], x['name'], x['n_ald']) for x in sucos if x['count'] is None])
por_suco = {x['no']: x for x in sucos}
print('aldeia munisípiu la hanesan:', [x['no'] for x in aldeias if por_suco[x['suco']]['mun'] != x['mun']][:5])

# bloku kada suco = husi liña aldeia primeiru to'o ikus
alt = {}
for pg, ys in rows_pg.items():
	ys = sorted(ys)
	alt[pg] = (BOT[pg] - TOP[pg]) / len(ys)
for s in sucos:
	aa = [a for a in aldeias if a['suco'] == s['no']]
	s['ini'] = min(pos(a['page'], a['y']) - 0.5 for a in aa)
	s['fim'] = max(pos(a['page'], a['y']) + 0.5 for a in aa)
	s['aldeias'] = [a['name'] for a in aa]

# ── 3. Suco → Posto: DP (bloku kontínuu; label iha klaran) ──
for mun in dict.fromkeys(s['mun'] for s in sucos):
	ss = [s for s in sucos if s['mun'] == mun]
	L = [l for l in labels if l['mun'] == mun and l['page'] in ordem]
	L.sort(key=lambda l: pos(l['page'], l['y']))
	if not L:
		for s in ss:
			s['posto'], s['desvio'] = None, None
		continue
	c = [pos(l['page'], l['y']) for l in L]
	n, k = len(ss), len(L)
	GAP = 4                 # kustu bloku posto sein label (label la tama iha PDF)
	INF = float('inf')
	# dp[j][i]: label 0..j-1 uza ona, suco 0..i-1 kobre; bloku bele ho label (j avansa) ka sein label (gap)
	dp = [[INF] * (n + 1) for _ in range(k + 1)]
	bk = [[None] * (n + 1) for _ in range(k + 1)]
	dp[0][0] = 0
	for i in range(1, n + 1):
		for j in range(0, k + 1):
			for a in range(0, i):
				ini, fim = ss[a]['ini'], ss[i - 1]['fim']
				# bloku sein label: la bele iha label ruma iha laran
				if dp[j][a] < INF and not any(ini <= x <= fim for x in c):
					v = dp[j][a] + GAP
					if v < dp[j][i]:
						dp[j][i], bk[j][i] = v, (j, a, None)
				if j >= 1 and dp[j - 1][a] < INF and ini <= c[j - 1] <= fim:
					v = dp[j - 1][a] + abs(c[j - 1] - (ini + fim) / 2)
					if v < dp[j][i]:
						dp[j][i], bk[j][i] = v, (j - 1, a, j - 1)
	if dp[k][n] == INF:
		print('DP falla', mun)
		continue
	i, j = n, k
	while i > 0:
		pj, a, lab = bk[j][i]
		ini, fim = ss[a]['ini'], ss[i - 1]['fim']
		for x in ss[a:i]:
			if lab is None:
				x['posto'], x['desvio'] = None, None
			else:
				x['posto'], x['desvio'] = L[lab]['name'], round(abs(c[lab] - (ini + fim) / 2), 1)
		i, j = a, pj

json.dump({'sucos': sucos, 'aldeias': aldeias}, open(OUT, 'w'), ensure_ascii=False, indent=1)
for mun in dict.fromkeys(s['mun'] for s in sucos):
	grp = defaultdict(list)
	for s in sucos:
		if s['mun'] == mun:
			grp[(s['posto'], s['desvio'])].append(s['name'])
	print(f'\n{mun}')
	for (p, d), ns in grp.items():
		print(f'  {p} (desvio {d} liña, {len(ns)} suco): {", ".join(ns)}')
