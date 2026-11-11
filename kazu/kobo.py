"""Koneksaun KoboToolbox → SIBAR-RbR (SIBAR tarik dadus; la presiza webhook públiku).

Fluxu:
    Kobo (/api/v2/assets/<asset>/data/)  ──tarik JSON──▶  kobo_ba_lina()  ──▶  importa.valida()
      ──▶  importa.konfirma()  ──▶  Kazu foun (status Hein Verifikasaun)

Dedup: Kazu.kobo_uuid (Kobo "_uuid"). Submission ne'ebé import ona la import fali.
Reuza pipeline import Excel tomak (valida + konfirma): validasaun, lokalizasaun, GPS aproksimadu,
istória no notifikasaun hanesan.

Konfigurasaun (.env):
    KOBO_BASE_URL   ex. https://kf.kobotoolbox.org   (ka servidor Kobo organizasaun nian)
    KOBO_TOKEN      token API Kobo (Account → Security → API token). RAI IHA .env DE'IT.
    KOBO_ASSET_UID  UID formuláriu (husi URL projetu Kobo, ex. aXXXXXXXXXXXXXXXXXXXXXX)

IMPORTANTE: MAPA iha okos TENKE hadia tuir naran pergunta iha imi-nia formuláriu Kobo.
Hala'o uluk `python manage.py sync_kobo --dry-run` atu haree mapeamentu molok kria dadus.
"""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from django.conf import settings

logger = logging.getLogger('smkre')

TEMPU = 60                    # timeout segundu kada pedidu
PAJINA = 300                  # submission kada pájina


# ══════════════════════════════════════════════════════════════════
# MAPA: naran pergunta Kobo  →  naran kolun template SIBAR
# HADIA tuir formuláriu imi-nian! Haree submission ida (`sync_kobo --amostra`).
# Valór bele uza 'group/pergunta' se formuláriu iha grupu.
# ══════════════════════════════════════════════════════════════════
MAPA = {
	# SIBAR kolun        : Kobo pergunta (naran)
	'data_relatoriu':     'data_relatoriu',
	'data_akontesimentu': 'data_akontesimentu',
	'munisipiu':          'munisipiu',
	'postu':              'postu',
	'suku':               'suku',
	'aldeia':             'aldeia',
	'tipu_konflitu':      'tipu_konflitu',      # naran tipu (',' ka ' ' separa se barak)
	'tipu_seluk':         'tipu_seluk',
	'tipu_rai':           'tipu_rai',
	'deskrisaun':         'deskrisaun',
	'titulu':             'titulu',
	'observasaun':        'observasaun',
	'uma_kain':           'uma_kain',
	'mane':               'mane',
	'feto':               'feto',
	'total_ema':          'total_ema',
	'konsentimentu':      'konsentimentu',      # "Sin"/"yes"/"1" → True
}
# Pergunta geopoint Kobo (string "lat lon alt akur") → latitude + longitude
MAPA_GPS = 'gps'
# Valór ba konsentimentu ne'ebé signifika SIN
KONSENTIMENTU_SIN = {'sin', 'yes', 'true', '1', 'loos', 'konsente'}


def _kfg(sub, naran):
	"""Foti valór husi submission Kobo; suporta 'grupu/pergunta' no naran rasik."""
	if naran in sub:
		return sub[naran]
	ikus = naran.split('/')[-1]                  # Kobo dalaruma uza naran kompletu grupu/pergunta
	for k, v in sub.items():
		if k.split('/')[-1] == ikus:
			return v
	return None


def kobo_ba_lina(sub, n):
	"""Submission Kobo (dict) → liña template SIBAR (dict ba importa.valida)."""
	d = {'_lina': n, '_kobo_uuid': sub.get('_uuid') or sub.get('meta/instanceID') or ''}
	for kolun, pergunta in MAPA.items():
		v = _kfg(sub, pergunta)
		if v is None or v == '':
			continue
		if kolun == 'konsentimentu':
			d[kolun] = 'Sin' if str(v).strip().lower() in KONSENTIMENTU_SIN else 'Lae'
		elif kolun == 'tipu_konflitu':
			d[kolun] = str(v).replace(';', ',')  # Kobo multi-select = "a b c" ka "a;b" → valida separa
		else:
			d[kolun] = v
	gps = _kfg(sub, MAPA_GPS)
	if gps:
		parte = str(gps).split()
		if len(parte) >= 2:
			d['latitude'], d['longitude'] = parte[0], parte[1]
	return d


# ══════════════════════════════════════════════════════════════════
# Kliente API Kobo (urllib stdlib; respeita proxy husi environment)
# ══════════════════════════════════════════════════════════════════
def _config():
	base = getattr(settings, 'KOBO_BASE_URL', '') or ''
	token = getattr(settings, 'KOBO_TOKEN', '') or ''
	asset = getattr(settings, 'KOBO_ASSET_UID', '') or ''
	if not (base and token and asset):
		raise RuntimeError('Konfigurasaun Kobo la kompletu: hatama KOBO_BASE_URL, KOBO_TOKEN no KOBO_ASSET_UID iha .env.')
	return base.rstrip('/'), token, asset


def _get(url, token):
	req = urllib.request.Request(url, headers={'Authorization': f'Token {token}', 'Accept': 'application/json'})
	with urllib.request.urlopen(req, timeout=TEMPU) as r:      # noqa: S310 (URL husi config, la'ós input)
		return json.loads(r.read().decode('utf-8'))


def buka_submissions(limite=None):
	"""Tarik submission hotu (ka to'o `limite`) husi Kobo. Retorna lista dict."""
	base, token, asset = _config()
	url = f'{base}/api/v2/assets/{asset}/data/?format=json&limit={PAJINA}'
	hotu = []
	# Paginasaun: Kobo fó "next" to'o rohan
	while url:
		data = _get(url, token)
		hotu.extend(data.get('results', []))
		if limite and len(hotu) >= limite:
			return hotu[:limite]
		url = data.get('next')
	return hotu


# ══════════════════════════════════════════════════════════════════
# Sync: tarik → valida → konfirma (kria Kazu)
# ══════════════════════════════════════════════════════════════════
def sync(user, dry_run=True, limite=None):
	"""Tarik submission foun husi Kobo no kria Kazu. dry_run=True: valida de'it, la kria.

	Retorna dict rezumu: {total, foun, kria, sala, erru:[...], amostra:[...]}.
	"""
	from kazu.importa import valida, konfirma, MAX_LINA
	from kazu.models import Kazu, KazuImport

	subs = buka_submissions(limite=limite)
	iha_ona = set(Kazu.objects.exclude(kobo_uuid=None).values_list('kobo_uuid', flat=True))
	foun = [s for s in subs if (s.get('_uuid') or '') and (s.get('_uuid') not in iha_ona)]
	rezumu = {'total': len(subs), 'foun': len(foun), 'kria': 0, 'sala': 0, 'erru': [], 'dry_run': dry_run}
	if not foun:
		return rezumu
	if len(foun) > MAX_LINA:
		foun = foun[:MAX_LINA]
		rezumu['avizu'] = f'Submission barak liu; prosesa {MAX_LINA} dahuluk.'

	lina, uuids = [], {}
	for i, s in enumerate(foun, start=1):
		d = kobo_ba_lina(s, i)
		uuids[i] = d['_kobo_uuid']
		lina.append(d)
	rez = valida(lina)
	for r in rez:
		r['dadus']['kobo_uuid'] = uuids.get(r['lina']) or None
		if not r['ok']:
			rezumu['sala'] += 1
			rezumu['erru'].append({'uuid': uuids.get(r['lina']), 'erru': r['erru']})

	rezumu['amostra'] = [{'uuid': uuids.get(r['lina']), 'ok': r['ok'], 'rezumu': r.get('rezumu'), 'erru': r['erru']} for r in rez[:5]]
	if dry_run:
		return rezumu

	imp = KazuImport.objects.create(
		naran_file=f'Kobo {getattr(settings, "KOBO_ASSET_UID", "") or "import"}', sha256='', dadus=rez, created_by=user,
		total=len(rez), total_ok=sum(1 for r in rez if r['ok']),
		total_aproksimadu=sum(1 for r in rez if r['ok'] and r['dadus']['gps_aproksimadu']))
	rezumu['kria'] = konfirma(imp, user)
	logger.info(f'Sync Kobo: kria {rezumu["kria"]} kazu husi {rezumu["foun"]} submission foun (husi {user.username})')
	return rezumu
