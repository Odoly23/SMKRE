"""
Dadus portal públiku (fatin IDA deit). Regra privasidade:

	1. Kazu aprovadu ona (Superadmin) deit: APPROVED / COMPLETED
	2. Ho konsentimentu, no la marka "La publika iha portal públiku"
	3. Agregadu deit — la iha naran, foto, GPS ka detalla kazu ida-idak
	4. Númeru 1–2 → "< 3" (la haruka númeru loos ba browser)
	5. Populasaun afetada hatudu deit bainhira kazu ≥ 3 iha grupu ne'e
"""
from datetime import date
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Sum, Max
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from custom.models import Munisipiu, Suku, TipuKonflitu
from kazu.models import Kazu, UmaKainAfetada, APPROVED, COMPLETED

STATUS_PUBLIKU = [APPROVED, COMPLETED]
CACHE_SEGUNDU = 600                  # production: minutu 10 (DEBUG: la iha cache, atu teste lokál haree kedas)


def limite():
	return settings.PORTAL_LIMITE_SUBAR


def portal_queryset():
	return Kazu.objects.filter(status__in=STATUS_PUBLIKU, konsentimentu=True, la_publika=False)


def subar(n):
	# {n, label}: n=None bainhira 1–2 (subar)
	n = n or 0
	if 0 < n < limite():
		return {'n': None, 'label': f'< {limite()}'}
	return {'n': n, 'label': str(n)}


def limpa_filtru(params):
	# Filtru husi URL: valida hotu (valór la validu = la uza)
	f = {}
	code = (params.get('munisipiu') or '').upper()[:5]
	if code and Munisipiu.active.filter(code=code).exists():
		f['munisipiu'] = code
	try:
		tipu = int(params.get('tipu') or 0)
		if tipu and TipuKonflitu.active.filter(pk=tipu).exists():
			f['tipu'] = tipu
	except (TypeError, ValueError):
		pass
	try:
		tinan = int(params.get('tinan') or 0)
		if 2000 <= tinan <= date.today().year:
			f['tinan'] = tinan
	except (TypeError, ValueError):
		pass
	return f


def _aplika(qs, f, sein=None):
	# sein: filtru ida ne'ebé la aplika (gráfiku ida hatudu opsaun hotu ba nia dimensaun rasik)
	if f.get('munisipiu') and sein != 'munisipiu':
		qs = qs.filter(munisipiu__code=f['munisipiu'])
	if f.get('tipu') and sein != 'tipu':
		qs = qs.filter(tipu_konflitu__id=f['tipu'])
	if f.get('tinan') and sein != 'tinan':
		qs = qs.filter(data_relatoriu__year=f['tinan'])
	return qs.distinct()


def _konta(qs, campo):
	# {valór campo: total kazu} — order_by(): Meta.ordering la tama iha GROUP BY
	return {r[campo]: r['n'] for r in qs.order_by().values(campo).annotate(n=Count('id', distinct=True))}


def estatistika(params):
	f = limpa_filtru(params)
	chave = 'portal:' + translation.get_language() + ':' + ':'.join(f'{k}={v}' for k, v in sorted(f.items()))
	if settings.DEBUG:
		return _kalkula(f)
	data = cache.get(chave)
	if data is None:
		data = _kalkula(f)
		cache.set(chave, data, CACHE_SEGUNDU)
	return data


def _kalkula(f):
	base = portal_queryset()
	kazu = _aplika(base, f)
	total = kazu.count()

	# KPI
	afe = UmaKainAfetada.objects.filter(kazu__in=kazu).aggregate(uma=Sum('uma_kain'), ema=Sum('total_ema'))
	hatudu_afetadu = total >= limite()
	kpi = {
		'total': subar(total),
		'uma_kain': (afe['uma'] or 0) if hatudu_afetadu else None,
		'ema': (afe['ema'] or 0) if hatudu_afetadu else None,
		'munisipiu': len([n for n in _konta(kazu, 'munisipiu_id').values() if n]),
	}

	# Kada munisípiu (la aplika filtru munisípiu: hatudu hotu, ida hili mak destaka)
	por_mun = _konta(_aplika(base, f, sein='munisipiu'), 'munisipiu_id')
	munisipiu = [dict({'code': m.code, 'name': m.name}, **subar(por_mun.get(m.pk, 0))) for m in Munisipiu.active.all()]

	# Kada tipu konflitu
	por_tipu = _konta(_aplika(base, f, sein='tipu'), 'tipu_konflitu__id')
	tipu = [dict({'id': t.pk, 'name': t.name}, **subar(por_tipu.get(t.pk, 0))) for t in TipuKonflitu.active.all()]

	# Kada tinan (data relatóriu)
	por_tinan = {}
	for r in _aplika(base, f, sein='tinan').exclude(data_relatoriu=None).order_by().values('data_relatoriu__year').annotate(n=Count('id', distinct=True)):
		por_tinan[r['data_relatoriu__year']] = r['n']
	tinan = [dict({'tinan': y}, **subar(por_tinan[y])) for y in sorted(por_tinan)]

	# Populasaun afetada kada munisípiu (grupu ho kazu ≥ limite deit)
	afetadu = []
	kazu_mun = _konta(kazu, 'munisipiu_id')
	rows = UmaKainAfetada.objects.filter(kazu__in=kazu).order_by().values('kazu__munisipiu_id').annotate(
		mane=Sum('mane'), feto=Sum('feto'), labarik=Sum('labarik'), uma=Sum('uma_kain'))
	naran = {m.pk: m for m in Munisipiu.active.all()}
	for r in rows:
		mun = naran.get(r['kazu__munisipiu_id'])
		if mun and kazu_mun.get(mun.pk, 0) >= limite():
			afetadu.append({'code': mun.code, 'name': mun.name, 'mane': r['mane'] or 0, 'feto': r['feto'] or 0,
				'labarik': r['labarik'] or 0, 'uma_kain': r['uma'] or 0})
	afetadu.sort(key=lambda x: -(x['mane'] + x['feto']))

	# Kada suku (bainhira hili munisípiu)
	suku = []
	if f.get('munisipiu'):
		por_suku = _konta(kazu, 'suku_id')
		nomes = dict(Suku.objects.filter(pk__in=[k for k in por_suku if k]).values_list('pk', 'name'))
		for pk, n in sorted(por_suku.items(), key=lambda x: -x[1]):
			suku.append(dict({'name': nomes.get(pk) or _('Suku seidauk rejista')}, **subar(n)))

	atualiza = portal_queryset().aggregate(d=Max('approved_at'))['d']
	return {
		'filtru': f, 'kpi': kpi, 'munisipiu': munisipiu, 'tipu': tipu, 'tinan': tinan,
		'afetadu': afetadu, 'suku': suku, 'limite': limite(),
		'atualiza': timezone.localtime(atualiza).strftime('%d/%m/%Y') if atualiza else None,
	}
