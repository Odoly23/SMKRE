"""
Formatu baze dadus sentrál RbR (Airtable "Kazu Hotu") ⇄ SIBAR-RbR.

Import: CSV / Excel ho kabesallu Airtable → liña ho naran kolun interna (kazu/importa.py valida no kria).
Export: kazu SIBAR → kolun hanesan Airtable (bele import fali) + kolun SIBAR iha ikus.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Kolun Airtable tuir orden (kabesallu hanesan file "Baze Central - Kazu Hotu")
H_ID = 'Identifikasaun kazu'
H_NUMERU = 'Kazu nia numero'
H_REF = 'Numero Referensia Kazu (auto)'
KABESALLU = [
	H_ID, H_NUMERU, H_REF, 'Tinan Kazu Hahu', 'Data Simu Kazu iha RBR', 'Tinan Simu Kazu iha RBR', 'Kazu', 'Tipu Kazu',
	'Verified', 'Observasaun kona-ba tipu kazu',
	"Projetu (karik kazu ne'e tipu Governu foti rai - foti atu hari'i saida?)",
	"Entidade ne'ebe foti rai (karik kazu ne'e tipu Governu foti rai - foti atu hari'i saida?)",
	'Entidade Benefisiariu', 'Munisipiu', 'Postu Administrativu', 'Suku', 'Aldeia', 'Enderesu ka Deskrisaun Fatin ',
	'Pontu Kordenadu (GPS)', 'Rai nia Luan (Metru ka Hektar)', 'Rai nia luan (M)', 'Rai nia luan (ha)',
	'Dadus Uma Kain iha ka lae?', 'Uma Kain afetadu hira', 'Total Ema', 'Feto ', 'Mane', 'Labarik',
	'Idozu (tinan 60 ba leten)', 'Ema ho defisiensia', 'Fontes Dadus Uma Kain', 'Observasaun kona-ba dadus ema afetadu',
	'Naran fokal point RBR nian', 'Numor Telemovel Fokal Point', 'Organizasaun', 'Enderesu (organizasaun nian)',
	'Tipu Fokal Point', "Organizasaun seluk ne'ebé halo akompaniamentu", 'Naran ema husi organizasaun seluk', 'Numor Kontaktu',
	'Naran portavos husi komunidade', 'Numero kontaktu portavos komunidade', 'Observasaun ruma kb portavos',
	'Rejistu iha tribunal?', 'Data rejistu iha tribunal', 'Se mak rejistu ka representa', 'Informasaun kontaktu advogadu nian',
	'Observasaun kona-ba prosesu tribunal', 'Iha ona desizaun husi tribunal', 'Desizaun hatun sá data?',
	'Simu Notifikasaun Ona?', 'Data simu notifikasaun', 'Observasaun kona-ba prosesu notifikasaun',
	'Eviksaun Akontese ona?', 'Data Eviksaun', 'Observasaun kona-ba eviksaun rasik', 'Data ikus cek status kazu',
	'Status Kazu', "RBR nia desizaun ba Kazu ne'e", 'Observasaun kona ba kazu',
	'Molok eviksaun iha konsultasaun ka lae?', 'Molok eviksaun iha notifikasaun klaru ka lae?',
	'Durante eviksaun uza forsa ka lae?', 'Akompanamentu ba Kazu', 'Formatu update kazu', 'Created By',
]

# Kolun testu simples: kabesallu Airtable → kampu interna (Kazu ka KazuSegimentu)
TESTU = {
	'Kazu': 'titulu', 'Observasaun kona-ba tipu kazu': 'deskrisaun',
	"Projetu (karik kazu ne'e tipu Governu foti rai - foti atu hari'i saida?)": 'projetu',
	"Entidade ne'ebe foti rai (karik kazu ne'e tipu Governu foti rai - foti atu hari'i saida?)": 'entidade_foti',
	'Munisipiu': 'munisipiu', 'Postu Administrativu': 'postu', 'Suku': 'suku', 'Aldeia': 'aldeia',
	'Enderesu ka Deskrisaun Fatin ': 'enderesu_fatin', 'Fontes Dadus Uma Kain': 'fonte_dadus_uma_kain',
	'Observasaun kona-ba dadus ema afetadu': 'observasaun_afetadu',
	'Naran fokal point RBR nian': 'fokal_naran', 'Numor Telemovel Fokal Point': 'fokal_telemovel',
	'Organizasaun': 'fokal_organizasaun', 'Enderesu (organizasaun nian)': 'fokal_enderesu',
	"Organizasaun seluk ne'ebé halo akompaniamentu": 'org_seluk', 'Naran ema husi organizasaun seluk': 'org_seluk_naran',
	'Numor Kontaktu': 'org_seluk_kontaktu', 'Naran portavos husi komunidade': 'portavos_naran',
	'Numero kontaktu portavos komunidade': 'portavos_kontaktu', 'Observasaun ruma kb portavos': 'portavos_observasaun',
	'Se mak rejistu ka representa': 'tribunal_representa', 'Informasaun kontaktu advogadu nian': 'advogadu_kontaktu',
	'Observasaun kona-ba prosesu tribunal': 'tribunal_observasaun', 'Observasaun kona-ba prosesu notifikasaun': 'notif_observasaun',
	'Observasaun kona-ba eviksaun rasik': 'observasaun_eviksaun', 'Observasaun kona ba kazu': 'observasaun_kazu',
}
NUMERU = {'Tinan Kazu Hahu': 'tinan_disputa_hahu', 'Uma Kain afetadu hira': 'uma_kain', 'Total Ema': 'total_ema', 'Feto ': 'feto',
	'Mane': 'mane', 'Labarik': 'labarik', 'Idozu (tinan 60 ba leten)': 'katuas_ferik', 'Ema ho defisiensia': 'defisiensia'}
# Opsaun (label Airtable → valór kampu nian label/kódigu; importa.py konverte label ba kódigu)
OPSAUN = {
	'Dadus Uma Kain iha ka lae?': 'iha_dadus_uma_kain', 'Eviksaun Akontese ona?': 'eviksaun_akontese',
	'Molok eviksaun iha konsultasaun ka lae?': 'konsultasaun_molok', 'Molok eviksaun iha notifikasaun klaru ka lae?': 'notifikasaun_klaru',
	'Durante eviksaun uza forsa ka lae?': 'uza_forsa', 'Rejistu iha tribunal?': 'tribunal_rejistu',
	'Iha ona desizaun husi tribunal': 'tribunal_desizaun', 'Simu Notifikasaun Ona?': 'notif_simu',
	'Tipu Fokal Point': 'fokal_tipu', 'Status Kazu': 'status_rezolusaun', "RBR nia desizaun ba Kazu ne'e": 'desizaun_rbr',
	'Entidade Benefisiariu': 'entidade_kategoria',
}
DATA = {'Data rejistu iha tribunal': 'tribunal_data', 'Desizaun hatun sá data?': 'tribunal_desizaun_data',
	'Data simu notifikasaun': 'notif_data', 'Data Eviksaun': 'data_eviksaun', 'Data ikus cek status kazu': 'data_ikus_cek'}
# Kampu observasaun ba seksaun ne'ebé data ka valór la klaru (testu orijinál la lakon)
OBS_DATA = {'tribunal_data': 'tribunal_observasaun', 'tribunal_desizaun_data': 'tribunal_observasaun',
	'notif_data': 'notif_observasaun', 'data_eviksaun': 'observasaun_eviksaun', 'data_ikus_cek': 'observasaun_kazu'}

# Tipu kazu Airtable → kódigu SIBAR (label la hanesan 100%: aksentu, "ou" / "ka")
TIPU_KAZU = {
	'DISPUTAENTREINDIVIDUHOKOMUNIDADE': 'IND-KOMUNIDADE', 'DISPUTAENTREINDIVIDUHOINDIVIDU': 'IND-IND',
	'GOVERNUFOTIKOMUNIDADENIARAIPRIVADU': 'GOV-RAI-PRIVADU', 'GOVERNUHASAIKOMUNIDADEHUSIRAIESTADU': 'GOV-RAI-ESTADU',
	'DISPUTAENTREKOMUNIDADEHOKOMUNIDADE': 'KOM-KOM', 'SELUK': 'SELUK',
}
SIN_LAE = {'IHA': 'SIN', 'SIN': 'SIN', 'LAIHA': 'LAE', 'LAE': 'LAE', 'LAHATENE': 'LAHATENE', 'LAHATENESTATUSATUAL': 'LAHATENE'}


def normal(t):
	# Komparasaun la sensível ba aksentu, espasu, pontuasaun no letra boot/kiik
	import unicodedata
	t = unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().upper()
	return re.sub(r'[^A-Z0-9]', '', t)


def e_airtable(kabesallu):
	k = {normal(h) for h in kabesallu}
	return normal(H_REF) in k or normal(H_ID) in k


def iha_dadus(row):
	# Liña ho dadus loos (la'ós rejistu mamuk ho ID automátiku de'it)
	auto = {normal(H_ID), normal(H_NUMERU), normal(H_REF), normal('Formatu update kazu'), normal('Created By'), normal('Rai nia luan (ha)')}
	return any(_t(v) and _t(v) not in ('0', '0.0') for k, v in row.items() if normal(k) not in auto)


def _t(v):
	return '' if v is None else str(v).strip()


def _tipu_kazu(v):
	n = normal(v)
	if n in TIPU_KAZU:
		return TIPU_KAZU[n]
	if n.startswith('DISPUTAENTREENTIDADELEGAL'):
		return 'ENTIDADE-LEGAL'
	if n.startswith('GOVERNUHASAIKOMUNIDADEHUSIRAIABANDONADU'):
		return 'GOV-RAI-ABANDONADU'
	return _t(v)                                    # importa.py buka tuir naran / kódigu


def data_testu(v, us_primeiru=False):
	"""Data husi testu Airtable: '22/9/2009', '1/16/12', '2023-05-02'… → (date ka None, testu orijinál se la klaru)."""
	if v in (None, ''):
		return None, ''
	if isinstance(v, datetime):
		return v.date(), ''
	if isinstance(v, date):
		return v, ''
	t = _t(v)
	primeiru = re.split(r'[\n;]|\s{2,}', t)[0].strip()
	m = re.fullmatch(r'(\d{4})-(\d{1,2})-(\d{1,2})', primeiru)
	if m:
		try:
			return date(int(m[1]), int(m[2]), int(m[3])), ('' if primeiru == t else t)
		except ValueError:
			return None, t
	m = re.fullmatch(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2}|\d{4})', primeiru)
	if not m:
		return None, t                              # "2001", "La hatene", "-" → rai iha observasaun
	a, b, y = int(m[1]), int(m[2]), int(m[3])
	y = y + (2000 if y < 50 else 1900) if y < 100 else y
	# Tinan dijitu 2 → formatu Airtable EUA (M/D/AA); tinan dijitu 4 → D/M/AAAA (hakerek iha Timor)
	orden = [(b, a), (a, b)] if (us_primeiru or len(m[3]) == 2) else [(a, b), (b, a)]
	for loron, fulan in orden:
		try:
			return date(y, fulan, loron), ('' if primeiru == t else t)
		except ValueError:
			continue
	return None, t


def _numeru(v):
	t = _t(v).replace(' ', '')
	if not t:
		return None
	try:
		n = Decimal(t.replace(',', '.'))
	except InvalidOperation:
		return None
	return n if n >= 0 else None


def rai_luan(metru, hektar, testu):
	"""(valór, unidade, nota). Prioridade: kolun metru → kolun hektar (> 0) → testu (ex. '17.000 M2', '2 ha')."""
	m = _numeru(metru)
	if m:
		return m.quantize(Decimal('0.01')), 'M2', ''
	h = _numeru(hektar)
	if h:
		return h.quantize(Decimal('0.01')), 'HA', ''
	t = _t(testu)
	if not t:
		return None, '', ''
	so = re.fullmatch(r'\s*([\d.,\s]+)\s*(m2|m²|metru|m|ha|hektar|hectare)?\s*\.?\s*', t, re.I)
	if so:
		num = re.sub(r'\s', '', so[1])
		if re.fullmatch(r'\d{1,3}([.,]\d{3})+', num):     # separadór milhar: 17.000 / 10,775
			num = re.sub(r'[.,]', '', num)
		n = _numeru(num)
		unid = 'HA' if (so[2] or '').lower() in ('ha', 'hektar', 'hectare') else 'M2'
		if n:
			return n.quantize(Decimal('0.01')), unid, ''
	return None, '', t                              # '12 X 6 M' → nota de'it


def lina_interna(row):
	"""Liña Airtable {kabesallu: valór} → {kolun interna: valór} ba importa.valida + '_nota', '_avizu', meta."""
	kab = {normal(k): v for k, v in row.items()}
	g = lambda h: kab.get(normal(h))
	d, nota, avizu = {}, [], []
	for h, c in TESTU.items():
		if _t(g(h)):
			d[c] = _t(g(h))
	for h, c in NUMERU.items():
		n = _numeru(g(h))
		if n is not None:
			d[c] = int(n)
	for h, c in OPSAUN.items():
		v = _t(g(h))
		if not v:
			continue
		if c == 'entidade_kategoria':
			partes = [p.strip() for p in v.split(',') if p.strip()]
			v = partes[0].replace('Kompanhia', 'Kompañia')
			if len(partes) > 1:
				nota.append('Entidade benefisiáriu: ' + ', '.join(partes))
		elif c == 'tribunal_rejistu' and normal(v).startswith('AGORADADAUN'):
			v = 'DADAUN'
		else:
			v = SIN_LAE.get(normal(v), v)
		d[c] = v
	for h, c in DATA.items():
		dt, orij = data_testu(g(h))
		if dt:
			d[c] = dt.isoformat()
		if orij:
			obs = OBS_DATA[c]
			d[obs] = (d.get(obs, '') + '\n' if d.get(obs) else '') + f'[{h.strip()}: {orij}]'
	# Tipu kazu
	if _t(g('Tipu Kazu')):
		# Tipu ida ka barak (export SIBAR separa ho ";") → kódigu
		d['tipu_konflitu'] = ';'.join(_tipu_kazu(t) for t in _t(g('Tipu Kazu')).split(';') if t.strip())
		if 'SELUK' in d['tipu_konflitu'].split(';') and not d.get('deskrisaun'):
			avizu.append('Tipu "Seluk" la iha esplikasaun.')
		if 'SELUK' in d['tipu_konflitu'].split(';'):
			d['tipu_seluk'] = (d.get('deskrisaun') or 'Seluk')[:255]
	# Data simu kazu: data (D/M/AAAA) ka tinan de'it
	dt, orij = data_testu(g('Data Simu Kazu iha RBR'))
	tinan = _numeru(g('Tinan Simu Kazu iha RBR'))
	if dt:
		d['data_relatoriu'] = dt.isoformat()
	elif tinan:
		d['data_relatoriu'] = date(int(tinan), 1, 1).isoformat()
		nota.append(f'Data simu kazu: tinan {int(tinan)} de\'it (data la iha iha Airtable).')
	if orij:
		nota.append(f'Data simu kazu (Airtable): {orij}')
	# Rai nia luan
	luan, unid, testu = rai_luan(g('Rai nia luan (M)'), g('Rai nia luan (ha)'), g('Rai nia Luan (Metru ka Hektar)'))
	if luan is not None:
		d['rai_luan'], d['rai_luan_unidade'] = str(luan), unid
	if testu:
		nota.append(f'Rai nia luan (Airtable): {testu}')
	# GPS: "lat, lng" (export SIBAR) ka link Google Maps naruk (@lat,lng / q=lat,lng); link badak → nota, fatin aproksimadu
	gps = _t(g('Pontu Kordenadu (GPS)'))
	m = re.search(r'(?:^|[@=/\s])(-?\d{1,2}\.\d+)\s*,\s*(-?\d{2,3}\.\d+)', gps)
	if m:
		d['latitude'], d['longitude'] = m[1], m[2]
	elif gps:
		nota.append('GPS (Airtable): ' + gps)
	if _t(g('Akompanamentu ba Kazu')):
		d['observasaun_kazu'] = (d.get('observasaun_kazu', '') + '\n' if d.get('observasaun_kazu') else '') + \
			'Akompañamentu (Airtable): ' + _t(g('Akompanamentu ba Kazu')).strip('"')
	d['titulu'] = d.get('titulu') or _t(g(H_ID))
	d['observasaun'] = '\n'.join(nota)
	d['_referensia'] = _t(g(H_REF))[:30] or None
	d['_verifikadu'] = normal(g('Verified')) in ('CHECKED', 'TRUE', 'SIN', '1', 'YES')
	d['_avizu'] = avizu
	d['_airtable'] = True
	return d


# ══════════════ Export (kolun Airtable) ══════════════
def _label(obj, campo):
	if obj is None:
		return ''
	v = getattr(obj, campo)
	if v in (None, ''):
		return ''
	f = obj._meta.get_field(campo)
	if f.choices:
		label = str(getattr(obj, f'get_{campo}_display')())
		seluk = getattr(obj, f'{campo}_seluk', '') if v == 'SELUK' else ''
		return f'{label}: {seluk}' if seluk else label
	if hasattr(v, 'strftime'):
		return v.strftime('%d/%m/%Y')
	return v


def lina_export(k, subar=()):
	"""Kazu → lista valór tuir KABESALLU (kontaktu pesoál iha `subar` sai mamuk)."""
	seg = getattr(k, 'segimentu', None) if hasattr(k, 'segimentu') else None
	af = list(k.afetadu.all())
	soma = lambda c: sum(getattr(a, c) or 0 for a in af) if any(getattr(a, c) is not None for a in af) else ''
	ref = k.referensia_rbr or k.kode or ''
	tipu = list(k.tipu_konflitu.all())
	val = {
		H_ID: k.titulu or ref, H_NUMERU: ref.split('/')[-1] if k.referensia_rbr else '', H_REF: ref,
		'Tinan Kazu Hahu': k.tinan_disputa_hahu or '', 'Data Simu Kazu iha RBR': _label(k, 'data_relatoriu'),
		'Tinan Simu Kazu iha RBR': k.data_relatoriu.year if k.data_relatoriu else '', 'Kazu': k.titulu,
		'Tipu Kazu': '; '.join(t.name for t in tipu), 'Verified': 'checked' if k.status in ('VERIFIED', 'APPROVED', 'COMPLETED') else '',
		'Munisipiu': k.munisipiu.name, 'Postu Administrativu': k.postu.name if k.postu else '',
		'Suku': k.suku.name if k.suku else '', 'Aldeia': k.aldeia.name if k.aldeia else '',
		'Pontu Kordenadu (GPS)': f'{k.latitude}, {k.longitude}' if k.latitude is not None else '',
		'Rai nia Luan (Metru ka Hektar)': f'{k.rai_luan} {k.get_rai_luan_unidade_display()}' if k.rai_luan is not None else '',
		'Rai nia luan (M)': float(k.rai_luan) if k.rai_luan is not None and k.rai_luan_unidade == 'M2' else '',
		'Rai nia luan (ha)': float(k.rai_luan) if k.rai_luan is not None and k.rai_luan_unidade == 'HA' else '',
		'Dadus Uma Kain iha ka lae?': {'SIN': 'Iha', 'LAE': 'Laiha'}.get(k.iha_dadus_uma_kain, _label(k, 'iha_dadus_uma_kain')),
		'Akompanamentu ba Kazu': '', 'Formatu update kazu': '', 'Created By': str(getattr(getattr(k.created_by, 'pesoaluser', None), 'pesoal', '') or k.created_by.username),
		'Entidade Benefisiariu': _label(k, 'entidade_kategoria'),
	}
	for h, c in NUMERU.items():
		if c == 'tinan_disputa_hahu':
			continue
		val[h] = soma(c)
	for h, c in list(TESTU.items()) + list(OPSAUN.items()) + list(DATA.items()):
		if h in val:
			continue
		obj = k if hasattr(k, c) else seg                # kampu segimentu (tribunál, fokal…)
		val[h] = '' if c in subar else _label(obj, c)
	return [val.get(h, '') for h in KABESALLU]
