"""
Poligon rai: validasaun no kalkulu luan / keliling / naruk / luan-badak.
Rumus luan no distánsia hanesan Turf.js (@turf/area, @turf/length) → númeru iha browser no server hanesan.
Server mak fonte loos: browser hatudu de'it, server kalkula fali molok rai.
"""
import math
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _
from shapely.geometry import Polygon, shape, mapping
from shapely.ops import unary_union
from shapely.validation import explain_validity

from kazu.forms import TL_LAT, TL_LON

EARTH_RADIUS = 6371008.8          # @turf/helpers earthRadius (m)
MAX_BIDANG = 20
MAX_PONTU = 500                   # kada bidang
M2_HA = 10000


# ── Rumus Turf.js ──
def _ring_area(coords):
	# @turf/area ringArea: área esférika ba anel ida (m²)
	n = len(coords) - 1
	if n <= 2:
		return 0.0
	total = 0.0
	for i in range(n):
		lower = coords[i]
		middle = coords[0 if i + 1 == n else i + 1]
		upper = coords[(i + 2) % n if i + 2 >= n else i + 2]
		total += (math.radians(upper[0]) - math.radians(lower[0])) * math.sin(math.radians(middle[1]))
	return abs(total * EARTH_RADIUS * EARTH_RADIUS / 2)


def area_m2(geom):
	# Polygon ka MultiPolygon (shapely) → m²
	polys = getattr(geom, 'geoms', [geom])
	total = 0.0
	for p in polys:
		if p.is_empty or p.geom_type != 'Polygon':
			continue
		total += _ring_area(list(p.exterior.coords))
		total -= sum(_ring_area(list(r.coords)) for r in p.interiors)
	return total


def distansia_m(a, b):
	# @turf/distance (haversine)
	dlat, dlon = math.radians(b[1] - a[1]), math.radians(b[0] - a[0])
	h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a[1])) * math.cos(math.radians(b[1])) * math.sin(dlon / 2) ** 2
	return 2 * EARTH_RADIUS * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def _naruk_luan(poly):
	# Retángulu minimu (rotadu) iha metru lokál → naruk (sisi boot) no luan-badak (sisi kiik)
	lon0, lat0 = poly.centroid.x, poly.centroid.y
	kx = math.radians(1) * EARTH_RADIUS * math.cos(math.radians(lat0))
	ky = math.radians(1) * EARTH_RADIUS
	lokal = Polygon([((x - lon0) * kx, (y - lat0) * ky) for x, y in poly.exterior.coords])
	rect = list(lokal.minimum_rotated_rectangle.exterior.coords)
	sisi = sorted([math.dist(rect[0], rect[1]), math.dist(rect[1], rect[2])])
	return sisi[1], sisi[0]


def metrika(poly):
	coords = list(poly.exterior.coords)
	keliling = sum(distansia_m(coords[i], coords[i + 1]) for i in range(len(coords) - 1))
	naruk, luan_badak = _naruk_luan(poly)
	return {'luan_m2': round(area_m2(poly), 2), 'keliling_m': round(keliling, 2),
		'naruk_m': round(naruk, 2), 'lebar_m': round(luan_badak, 2)}


# ── Validasaun ──
def valida(data):
	"""GeoJSON (FeatureCollection / Feature / Polygon / MultiPolygon) → lista Polygon shapely. Erru → ValidationError."""
	if not data:
		return []
	if not isinstance(data, dict):
		raise ValidationError(_('Poligon la validu.'))
	if data.get('type') == 'FeatureCollection':
		geoms = [f.get('geometry') for f in data.get('features') or [] if isinstance(f, dict)]
	elif data.get('type') == 'Feature':
		geoms = [data.get('geometry')]
	else:
		geoms = [data]
	polys = []
	for g in geoms:
		try:
			s = shape(g)
		except Exception:
			raise ValidationError(_('Poligon la validu.'))
		if s.geom_type == 'MultiPolygon':
			polys.extend(s.geoms)
		elif s.geom_type == 'Polygon':
			polys.append(s)
		else:
			raise ValidationError(_('Poligon de\'it mak bele rai.'))
	if len(polys) > MAX_BIDANG:
		raise ValidationError(_('Bidang rai máximu %(n)s kada kazu.') % {'n': MAX_BIDANG})
	for i, p in enumerate(polys, 1):
		coords = list(p.exterior.coords)
		if len(set(coords[:-1])) < 3:
			raise ValidationError(_('Bidang %(i)s: presiza pontu 3 ka liu.') % {'i': i})
		if len(coords) > MAX_PONTU + 1:
			raise ValidationError(_('Bidang %(i)s: pontu máximu %(n)s.') % {'i': i, 'n': MAX_PONTU})
		for x, y in coords:
			if not (float(TL_LON[0]) <= x <= float(TL_LON[1]) and float(TL_LAT[0]) <= y <= float(TL_LAT[1])):
				raise ValidationError(_('Bidang %(i)s: pontu la iha territóriu Timor-Leste.') % {'i': i})
		if not p.is_valid:
			raise ValidationError(_('Bidang %(i)s: liña kruza malu (%(r)s). Muda pontu atu liña la kruza.') % {'i': i, 'r': explain_validity(p)})
		if p.area == 0:
			raise ValidationError(_('Bidang %(i)s: presiza pontu 3 ka liu.') % {'i': i})
	return polys


def kalkula(data):
	"""Retorna (FeatureCollection normalizadu ho metrika kada bidang, total luan m², total keliling m)."""
	polys = valida(data)
	if not polys:
		return None, None, None
	features = []
	for i, p in enumerate(polys, 1):
		p = Polygon([(round(x, 7), round(y, 7)) for x, y in p.exterior.coords])
		features.append({'type': 'Feature', 'properties': dict(metrika(p), bidang=i), 'geometry': mapping(p)})
	# Luan total: bidang ne'ebé sobrepoin la konta dala rua (hanesan turf.union)
	uniaun = unary_union([shape(f['geometry']) for f in features])
	total_luan = round(area_m2(uniaun), 2)
	total_keliling = round(sum(f['properties']['keliling_m'] for f in features), 2)
	fc = {'type': 'FeatureCollection', 'features': [dict(f, geometry=_lista(f['geometry'])) for f in features]}
	return fc, total_luan, total_keliling


def _lista(geom):
	# mapping() fó tuple → JSON lista
	return {'type': geom['type'], 'coordinates': [[list(c) for c in ring] for ring in geom['coordinates']]}


def luan_rai(m2):
	# Rai nia luan otomátiku: < 1 ha → m², ≥ 1 ha → ha
	m2 = Decimal(str(m2))
	if m2 >= M2_HA:
		return (m2 / M2_HA).quantize(Decimal('0.01')), 'HA'
	return m2.quantize(Decimal('0.01')), 'M2'


def aplika(kazu, data):
	"""Valida + kalkula + tau iha kazu (la rai). Poligon mamuk → hamoos poligon (rai_luan manuál fila)."""
	fc, luan, keliling = kalkula(data)
	kazu.poligon, kazu.poligon_luan_m2, kazu.poligon_keliling_m = fc, luan, keliling
	if fc:
		kazu.rai_luan, kazu.rai_luan_unidade = luan_rai(luan)
	return kazu


@transaction.atomic
def rai_poligon(kazu, user, data):
	from kazu.models import KazuHistoria
	antes = kazu.poligon_luan_m2
	aplika(kazu, data)
	kazu.save(update_fields=['poligon', 'poligon_luan_m2', 'poligon_keliling_m', 'rai_luan', 'rai_luan_unidade', 'updated_at'])
	n = len(kazu.poligon['features']) if kazu.poligon else 0
	nota = (_('Poligon rai: %(n)s bidang, %(m2)s m²') % {'n': n, 'm2': kazu.poligon_luan_m2}) if n else _('Poligon rai hamoos')
	if antes is not None and n:
		nota += ' (' + _('uluk') + f' {antes} m²)'
	KazuHistoria.objects.create(kazu=kazu, user=user, tipu=KazuHistoria.EDITA, status_foun=kazu.status, nota=nota[:255])
	return kazu
