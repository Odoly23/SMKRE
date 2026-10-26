"""ID HP (offline) no deteksaun kazu duplikadu.

ID HP: HP kria kódigu automátiku bainhira kazu foun (la presiza internet) → HP-AAMMDD-XXXXXX
  (data kria iha oras Dili + karakter 6 husi UUID). Server kalkula hanesan (smkre_offline.js: kodeHp).
  ID ofisiál RbR-MUN-TINAN-0000 nafatin server mak fó bainhira haruka.
Duplikadu: kazu seluk ho GPS besik (≤ 200 m) ka aldeia + tipu konflitu hanesan → avizu ba Admin.
"""
import math
from django.utils import timezone
from django.utils.translation import gettext as _

RAIU_M = 200
_GRAU = 0.0025          # ~275 m: filtru lalais iha base de dadus antes kalkula distánsia loos


def kode_hp_baze(kazu_id, kria_iha):
	data = timezone.localtime(kria_iha).strftime('%y%m%d')
	return f'HP-{data}-{kazu_id.hex[:6].upper()}'


def atribui_kode_hp(kazu, kria_iha):
	# Raru tebes: kódigu hanesan ona → aumenta karakter UUID
	from kazu.models import Kazu
	if kazu.kode_hp:
		return kazu.kode_hp
	kode, n = kode_hp_baze(kazu.id, kria_iha), 6
	while Kazu.objects.filter(kode_hp=kode).exclude(pk=kazu.pk).exists() and n < 32:
		n += 2
		kode = f'{kode[:10]}{kazu.id.hex[:n].upper()}'
	kazu.kode_hp = kode
	return kode


def distansia_m(lat1, lng1, lat2, lng2):
	r = 6371000
	p1, p2 = math.radians(lat1), math.radians(lat2)
	dp, dl = p2 - p1, math.radians(lng2 - lng1)
	a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
	return 2 * r * math.asin(math.sqrt(a))


def posivel_duplikadu(kazu, limite=5):
	"""Lista [{kazu, razaun, distansia}] — kazu seluk ne'ebé bele hanesan (la inklui kanseladu no 'la'ós duplikadu')."""
	from kazu.models import Kazu, CANCELED
	if kazu.pk is None or kazu._state.adding:
		return []
	qs = Kazu.objects.exclude(pk=kazu.pk).exclude(status=CANCELED) \
		.exclude(pk__in=kazu.duplikadu_la_os.values('pk')).select_related('munisipiu', 'suku', 'aldeia')
	rez = {}
	# GPS aproksimadu (sentru suku husi import) la konta: kazu barak iha pontu hanesan
	if kazu.latitude is not None and kazu.longitude is not None and not kazu.gps_aproksimadu:
		lat, lng = float(kazu.latitude), float(kazu.longitude)
		for k in qs.filter(gps_aproksimadu=False, latitude__range=(lat - _GRAU, lat + _GRAU), longitude__range=(lng - _GRAU, lng + _GRAU)):
			d = round(distansia_m(lat, lng, float(k.latitude), float(k.longitude)))
			if d <= RAIU_M:
				rez[k.pk] = {'kazu': k, 'distansia': d, 'razaun': _('GPS besik: %(m)s m') % {'m': d}}
	if kazu.aldeia_id:
		tipu = list(kazu.tipu_konflitu.values_list('pk', flat=True))
		if tipu:
			for k in qs.filter(aldeia_id=kazu.aldeia_id, tipu_konflitu__in=tipu).distinct():
				rez.setdefault(k.pk, {'kazu': k, 'distansia': None, 'razaun': _('Aldeia no tipu konflitu hanesan')})
	lista = sorted(rez.values(), key=lambda r: (r['distansia'] is None, r['distansia'] or 0, str(r['kazu'])))
	return lista[:limite]


def duplikadu_testu(kazu):
	# Testu badak ba notifikasaun / resposta API: "RbR-LIQ-2026-0003 (GPS besik: 40 m)"
	return [f'{d["kazu"]} ({d["razaun"]})' for d in posivel_duplikadu(kazu)]
