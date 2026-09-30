"""Konsensu metodu rua → CSV + Excel ba import (Diploma Ministerial 31/2026)."""
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

PT, LINHA, POSTU_CSV, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
A = json.load(open(PT))
B = json.load(open(LINHA))
sb = {s['no']: s for s in B['sucos']}
MUN_NARAN = {'AIL': 'Aileu', 'AIN': 'Ainaro', 'ATA': 'Ataúro', 'BAU': 'Baucau', 'BOB': 'Bobonaro', 'COV': 'Covalima',
	'DIL': 'Díli', 'ERM': 'Ermera', 'LAU': 'Lautém', 'LIQ': 'Liquiçá', 'MAN': 'Manatuto', 'MNF': 'Manufahi',
	'OEC': 'Oé-Cusse Ambeno (RAEOA)', 'VIQ': 'Viqueque'}


def norm(t):
	t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().upper()
	return re.sub(r'[^A-Z]', '', t)


# Postu iha sistema + postu foun husi DM 31/2026
postu = [dict(r, foun='') for r in csv.DictReader(open(POSTU_CSV, encoding='utf-8'))]
ALIAS = {'AILEU': 'AILEUVILA', 'HATOUDO': 'HATUDO', 'FATUBERLIU': 'FATUBERLIO', 'MACASSAR': 'PANTEMACASSAR',
	'PASABE': 'PASSABE', 'UATULARI': 'UATOLARI', 'LIQUICA': 'LIQUICA'}
FOUN = {('BAU', 'QUELICAIANTIGU'): ('BAU-07', 'Quelicai Antigu'), ('BAU', 'MATEBIAN'): ('BAU-08', 'Matebian'),
	('ERM', 'HATULIAA'): ('ERM-06', 'Hatulia A'), ('ERM', 'HATULIAB'): ('ERM-07', 'Hatulia B'),
	('LAU', 'LORE'): ('LAU-06', 'Loré'), ('LIQ', 'LOES'): ('LIQ-04', 'Loes')}
for (m, _k), (code, name) in FOUN.items():
	postu.append({'munisipiu': m, 'code': code, 'name': name, 'foun': 'SIN (DM 31/2026)'})
por_nome = {(p['munisipiu'], norm(p['name'])): p for p in postu}


def postu_de(mun, label):
	if mun == 'ATA':
		return por_nome[('ATA', 'ATAURO')]
	if not label:
		return None
	k = norm(label)
	if (mun, k) in FOUN:
		return por_nome[(mun, norm(FOUN[(mun, k)][1]))]
	return por_nome.get((mun, ALIAS.get(k, k)))


ROMANO = {'I', 'II', 'III', 'IV', 'V', 'VI'}
MINUS = {'DE', 'DA', 'DO', 'DOS', 'DAS', 'E'}


def titulu(t):
	# "SUCO LIURAI" → "Suco Liurai", "MAU-ULO" → "Mau-Ulo", "LORÉ II" → "Loré II", "ISOROLAI DE BAI" → "Isorolai de Bai"
	def palavra(w, i):
		if w in ROMANO:
			return w
		if i > 0 and w in MINUS:
			return w.lower()
		return '-'.join("'".join(p[:1].upper() + p[1:].lower() for p in x.split("'")) for x in w.split('-'))
	return ' '.join(palavra(w, i) for i, w in enumerate(t.split()))


# ── Suco ──
labels_pdf = defaultdict(set)
for s in A['sucos']:
	if s['posto']:
		labels_pdf[s['mun']].add(s['posto'])
dup = Counter((s['mun'], s['name']) for s in A['sucos'])
suku_rows, n_ver = [], 0
for s in sorted(A['sucos'], key=lambda x: x['no']):
	mun, p1, p2 = s['mun'], s['posto'], sb[s['no']]['posto']
	pa, pb = postu_de(mun, p1), postu_de(mun, p2)
	verifika, sujestaun = '', ''
	if mun == 'ATA' or (pa and pb and pa is pb):
		final = pa if mun != 'ATA' else postu_de('ATA', None)
	else:
		final = None
		verifika = 'SIN'
		if p1 is None and p2 is None or (mun in ('AIL', 'LAU') and (p1 is None or p2 is None)):
			usadu = {postu_de(mun, l)['code'] for l in labels_pdf[mun] if postu_de(mun, l)}
			livre = [f"{p['code']} {p['name']}" for p in postu if p['munisipiu'] == mun and p['code'] not in usadu and not p['foun']]
			sujestaun = 'Label posto la iha PDF. Hili: ' + ' / '.join(livre)
			outro = pa or pb
			if outro:
				sujestaun += f" (ka {outro['code']} {outro['name']})"
		else:
			opc = []
			for p in (pa, pb):
				if p and f"{p['code']} {p['name']}" not in opc:
					opc.append(f"{p['code']} {p['name']}")
			sujestaun = 'Suco iha fronteira entre posto rua. Hili: ' + ' / '.join(opc)
		n_ver += 1
	obs = []
	if s.get('obs'):
		obs.append(titulu(s['obs']))
	if dup[(mun, s['name'])] > 1:
		obs.append("Naran hanesan ho suco seluk iha munisípiu ne'e (kódigu la hanesan; PDF la hakerek I/II)")
	if s.get('no_pdf') and s['no_pdf'] != s['no']:
		obs.append(f"PDF hakerek númeru {s['no_pdf']} (salah-ketik)")
	if s.get('count_pdf', 1) is None or s['count'] is None:
		obs.append('Kolun NO ALDEIA mamuk iha PDF (konta husi tabela)')
	suku_rows.append({
		'munisipiu': mun, 'munisipiu_naran': MUN_NARAN[mun], 'no': s['no'], 'suku_code': f"{mun}-S{s['no']:03d}",
		'suku': titulu(s['name']), 'postu_code': final['code'] if final else '', 'postu': final['name'] if final else '',
		'verifika': verifika, 'sujestaun': sujestaun, 'n_aldeia': s['n_ald'], 'obs': '; '.join(obs),
	})

suku_code = {r['no']: r['suku_code'] for r in suku_rows}
aldeia_rows = [{'suku_code': suku_code[a['suco']], 'aldeia_code': f"{a['mun']}-A{a['no']:04d}", 'no': a['no'],
	'aldeia': titulu(a['name'])} for a in sorted(A['aldeias'], key=lambda x: x['no'])]

# ── Hakerek CSV ──
import os
os.makedirs(OUT, exist_ok=True)
CS = [('postu', ['munisipiu', 'code', 'name', 'foun'], postu),
	('suku', ['munisipiu', 'munisipiu_naran', 'no', 'suku_code', 'suku', 'postu_code', 'postu', 'verifika', 'sujestaun', 'n_aldeia', 'obs'], suku_rows),
	('aldeia', ['suku_code', 'aldeia_code', 'no', 'aldeia'], aldeia_rows)]
for nome, cols, rows in CS:
	with open(f'{OUT}/{nome}_dm31_2026.csv', 'w', encoding='utf-8', newline='') as f:
		w = csv.DictWriter(f, fieldnames=cols)
		w.writeheader()
		w.writerows(rows)

# ── Excel (ba edita VERIFIKA) ──
wb = Workbook()
KAB = PatternFill('solid', fgColor='0E8A68')
AMARELU = PatternFill('solid', fgColor='FFF3B0')
info = wb.active
info.title = 'Lee-uluk'
linhas = [
	'SMKRE — Munisípiu · Postu · Suku · Aldeia',
	'Fonte: Diploma Ministerial N.º 31/2026 (Jornal da República, Série I, N.º 26 D, 3 Julho 2026)',
	f'Suku: {len(suku_rows)} · Aldeia: {len(aldeia_rows)} · Postu: {len(postu)} · Suku VERIFIKA: {n_ver}',
	'',
	'1. Aba "Suku": liña kór-mean (verifika = SIN) → hakerek postu_code (haree aba "Postu" ka kolun sujestaun).',
	'2. Labele muda suku_code ka aldeia_code (kódigu ne\'e liga suku ho aldeia).',
	'3. Import: python manage.py import_wilayah wilayah_dm31_2026.xlsx --dry-run  (teste)  →  sein --dry-run (rai).',
	'4. Suku ho postu_code mamuk la tama; bele import fali depois prenxe (seguru, la duplika).',
]
for i, t in enumerate(linhas, start=1):
	info.cell(row=i, column=1, value=t).font = Font(bold=(i == 1), size=13 if i == 1 else 11)
info.column_dimensions['A'].width = 120
for nome, cols, rows in [CS[1], CS[2], CS[0]]:
	ws = wb.create_sheet({'suku': 'Suku', 'aldeia': 'Aldeia', 'postu': 'Postu'}[nome])
	ws.append(cols)
	for c in ws[1]:
		c.font, c.fill = Font(bold=True, color='FFFFFF'), KAB
	for r in rows:
		ws.append([r[c] for c in cols])
		if nome == 'suku' and r['verifika']:
			for c in ws[ws.max_row]:
				c.fill = AMARELU
	ws.freeze_panes = 'A2'
	ws.auto_filter.ref = ws.dimensions
	for col in ws.columns:
		ws.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or '')) for c in col) + 2))
	if nome == 'suku':
		dv = DataValidation(type='list', formula1=f"=Postu!$B$2:$B${len(postu) + 1}", allow_blank=True)
		ws.add_data_validation(dv)
		dv.add(f'F2:F{len(rows) + 1}')
wb.save(f'{OUT}/wilayah_dm31_2026.xlsx')
print(f'suku {len(suku_rows)} · aldeia {len(aldeia_rows)} · postu {len(postu)} · VERIFIKA {n_ver}')
