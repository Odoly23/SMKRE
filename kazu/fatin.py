"""Verifika GPS kazu ho fronteira munisípiu (avizu de'it — la bloku).

Fronteira iha main/static/main/geojson/timor_munisipiu.json simplifika (kB 15): tasi-ibun bele sala
to'o km 2–3 (ex. Cristo Rei, Tasitolu sai li'ur liña). Tan ne'e regra:
  1. GPS iha laran munisípiu SELUK → avizu (prova klaru la hanesan).
  2. GPS la iha laran munisípiu ida (tasi-ibun / tasi) → munisípiu besik liu; avizu de'it se ida ne'e
     la'ós munisípiu ne'ebé hili NO distánsia ba munisípiu hili > LIMITE_M.
Regra hanesan iha app offline (smkre_offline.js: munisipiuGPS) atu HP no server hatudu avizu hanesan.
"""
import json
import math
from functools import lru_cache
from django.conf import settings
from django.utils.translation import gettext as _

LIMITE_M = 3000
GEOJSON = settings.BASE_DIR / 'main' / 'static' / 'main' / 'geojson' / 'timor_munisipiu.json'


# fronteira munisípiu (shapely) tuir kódigu — lee dala ida de'it
@lru_cache(maxsize=1)
def _fronteira():
	from shapely.geometry import shape
	with open(GEOJSON, encoding='utf-8') as f:
		g = json.load(f)
	return {ft['properties']['code']: shape(ft['geometry']) for ft in g['features']}


# distánsia aproksimadu (metru) entre pontu no fronteira (grau → metru, latitude Timor ~ -8.5°)
def _metru(geom, pontu):
	from shapely.ops import nearest_points
	a, b = nearest_points(geom, pontu)
	dx = (a.x - b.x) * 111320 * math.cos(math.radians(pontu.y))
	dy = (a.y - b.y) * 110574
	return math.hypot(dx, dy)


# munisípiu tuir GPS: (kódigu ne'ebé iha pontu ka None, kódigu besik liu, distánsia ba munisípiu hili)
def munisipiu_gps(lat, lng, hili=None):
	from shapely.geometry import Point
	p = Point(float(lng), float(lat))
	fr = _fronteira()
	laran = next((c for c, s in fr.items() if s.contains(p)), None)
	besik = laran or min(fr, key=lambda c: fr[c].distance(p))
	dist = _metru(fr[hili], p) if hili in fr else None
	return laran, besik, dist


# testu avizu se GPS la tuir munisípiu kazu nian; '' bainhira di'ak ka la bele verifika
def avizu_munisipiu(lat, lng, munisipiu):
	if lat is None or lng is None or munisipiu is None:
		return ''
	try:
		laran, besik, dist = munisipiu_gps(lat, lng, munisipiu.code)
	except (OSError, ValueError, KeyError):
		return ''                                       # fronteira la iha: la avizu
	if dist is None:
		return ''                                       # munisípiu la iha mapa
	la_hanesan = (laran is not None and laran != munisipiu.code) or \
		(laran is None and besik != munisipiu.code and dist > LIMITE_M)
	if not la_hanesan:
		return ''
	from custom.models import Munisipiu
	naran = Munisipiu.objects.filter(code=besik).values_list('name', flat=True).first() or besik
	return _('Koordenada GPS iha %(gps)s, maibé kazu rejista iha %(mun)s. Favor verifika munisípiu ka GPS.') % {
		'gps': naran, 'mun': munisipiu.name}
