"""Relatóriu "Influensia no Advokasia" no relatóriu tabular (kazu tuir munisípiu).

Fatin IDA ba kalkulu no filtru: views (pájina) no lista kazu (klik númeru) uza funsaun hanesan,
entaun númeru iha relatóriu no total iha lista sempre hanesan.
"""
from django.db.models import Count, Q, Sum
from django.utils.translation import gettext as _, gettext_lazy as _l
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import Kazu, KazuSegimentu, UmaKainAfetada, KazuEntidade
from kazu.models.opsaun import SIN_LAE_CHOICES, ENTIDADE_CHOICES

# Tipu kazu "Governu foti komunidade nia rai privadu"
TIPU_GOV_FOTI = 'GOV-RAI-PRIVADU'
# Status rezolusaun (segimentu): grupu badak ba relatóriu tabular
REZ_REZOLVE = ['RES_FAMILIA', 'RES_TRIBUNAL', 'RES_MEDIASAUN', 'RES_ABANDONA', 'RES_KOMPENSASAUN']
REZ_GRUPU = [
	('seidauk', _l('Seidauk rezolve'), Q(segimentu__status_rezolusaun__in=['SEIDAUK', 'BALU_RESOLVE'])),
	('rezolve', _l('Rezolve ona'), Q(segimentu__status_rezolusaun__in=REZ_REZOLVE)),
	('abandona', _l('Abandona'), Q(segimentu__status_rezolusaun='ABANDONA')),
	('lahatene', _l('La hatene / laiha dadus'), Q(segimentu__status_rezolusaun__in=['LAHATENE', '']) | Q(segimentu__isnull=True)),
]
TRIB_GRUPU = [
	('sin', _l('Sin'), Q(segimentu__tribunal_rejistu='SIN')),
	('dadaun', _l('Rejistu hela'), Q(segimentu__tribunal_rejistu='DADAUN')),
	('lae', _l('Lae'), Q(segimentu__tribunal_rejistu='LAE')),
	('lahatene', _l('La hatene / laiha dadus'), Q(segimentu__tribunal_rejistu__in=['LAHATENE', '']) | Q(segimentu__isnull=True)),
]
EVIK_GRUPU = [
	('sin', _l('Sin'), Q(eviksaun__eviksaun_akontese='SIN')),
	('lae', _l('Lae'), Q(eviksaun__eviksaun_akontese='LAE')),
	('lahatene', _l('La hatene / laiha dadus'), Q(eviksaun__eviksaun_akontese__in=['LAHATENE', '']) | Q(eviksaun__isnull=True)),
]


def seidauk_rezolve():
	# Kazu seidauk rezolve: la iha status "Rezolve ona" ka "Abandona" (laiha dadus = seidauk)
	return ~Q(segimentu__status_rezolusaun__in=REZ_REZOLVE + ['ABANDONA'])


def filtru(grupu, valor):
	"""Q ba kolun ida iha relatóriu tabular (link ba lista). None = grupu / valór la iha."""
	if grupu == 'total':
		return Q()
	if grupu == 'tipu':
		return Q(tipu_konflitu__pk=valor) if str(valor).isdigit() else None
	tab = {'rez': REZ_GRUPU, 'trib': TRIB_GRUPU, 'evik': EVIK_GRUPU}.get(grupu)
	for k, _l, q in tab or []:
		if k == valor:
			return q
	return None


def label_filtru(grupu, valor):
	if grupu == 'total':
		return _('Total')
	if grupu == 'tipu':
		t = TipuKonflitu.objects.filter(pk=valor).first()
		return t.name if t else ''
	naran = {'rez': _('Status kazu'), 'trib': _('Rejistu iha tribunál'), 'evik': _('Eviksaun akontese')}[grupu]
	tab = {'rez': REZ_GRUPU, 'trib': TRIB_GRUPU, 'evik': EVIK_GRUPU}[grupu]
	return f'{naran}: ' + next((str(l) for k, l, _q in tab if k == valor), valor)


def _baze(qs):
	# report_queryset uza distinct(); agregasaun iha queryset foun ho pk de'it (la duplika)
	return Kazu.objects.filter(pk__in=qs.values('pk'))


def _konta(qs, campo, choices, sem=_l('La iha dadus')):
	"""[(kódigu, label, n)] tuir orden choices + mamuk, la hatudu n=0; ordena boot → ki'ik."""
	label = dict(choices)
	rez = {}
	for r in qs.values(campo).annotate(n=Count('pk', distinct=True)):
		k = r[campo] or ''
		rez[k] = rez.get(k, 0) + r['n']
	lista = [(k, str(label.get(k, sem)) if k else str(sem), n) for k, n in rez.items() if n]
	return sorted(lista, key=lambda x: -x[2])


def _soma_afetadu(qs):
	a = UmaKainAfetada.objects.filter(kazu__in=qs).aggregate(
		uma_kain=Sum('uma_kain'), mane=Sum('mane'), feto=Sum('feto'), labarik=Sum('labarik'), total=Sum('total_ema'))
	return {k: v or 0 for k, v in a.items()}


def _top(lista, n=2):
	# Testu badak: "Dili (87), Oecusse (13)"
	return ', '.join(f'{l} ({v})' for _k, l, v in lista[:n])


def advokasia(qs):
	"""Dadus ba pájina Influensia no Advokasia (seksaun hotu)."""
	kazu = _baze(qs)
	total = kazu.count()
	af = _soma_afetadu(kazu)
	laiha_uma = kazu.exclude(afetadu__uma_kain__gt=0).count()

	mun = [(m['munisipiu'], m['munisipiu__name'], m['n']) for m in
		kazu.values('munisipiu', 'munisipiu__name').annotate(n=Count('pk')).order_by('-n')]
	tipu = [(t['tipu_konflitu'], t['tipu_konflitu__name'], t['n']) for t in
		kazu.filter(tipu_konflitu__isnull=False).values('tipu_konflitu', 'tipu_konflitu__name').annotate(n=Count('pk', distinct=True)).order_by('-n')]
	tinan = {}
	for d, t in kazu.values_list('data_relatoriu', 'tinan_simu'):
		y = d.year if d else t
		tinan[y] = tinan.get(y, 0) + 1
	tinan_lista = [(y, str(y), tinan[y]) for y in sorted(k for k in tinan if k)]
	if tinan.get(None):
		tinan_lista.append(('', _('La hatene'), tinan[None]))

	# Status kazu (segimentu) no tribunál: kazu seidauk rezolve de'it
	rez_choices = KazuSegimentu.REZOLUSAUN_CHOICES
	status = _konta(kazu, 'segimentu__status_rezolusaun', rez_choices)
	seidauk = kazu.filter(seidauk_rezolve())
	tribunal = _konta(seidauk, 'segimentu__tribunal_rejistu', KazuSegimentu.TRIBUNAL_CHOICES)
	la_tribunal = seidauk.exclude(segimentu__tribunal_rejistu__in=['SIN', 'DADAUN'])
	tipu_la_trib = [(t['tipu_konflitu'], t['tipu_konflitu__name'], t['n']) for t in
		la_tribunal.filter(tipu_konflitu__isnull=False).values('tipu_konflitu', 'tipu_konflitu__name').annotate(n=Count('pk', distinct=True)).order_by('-n')]

	# Governu foti komunidade nia rai
	gov = kazu.filter(tipu_konflitu__code=TIPU_GOV_FOTI).distinct()
	gov_af = _soma_afetadu(gov)
	entidade = _konta(KazuEntidade.objects.filter(kazu__in=gov).exclude(entidade_kategoria=''), 'entidade_kategoria', ENTIDADE_CHOICES)

	# Eviksaun
	evik = kazu.filter(eviksaun__eviksaun_akontese='SIN')
	evik_af = _soma_afetadu(evik)
	ev = {c: _konta(evik, f'eviksaun__{c}', SIN_LAE_CHOICES) for c in ('konsultasaun_molok', 'notifikasaun_klaru', 'uza_forsa')}

	def pct(n, d):
		return round(100 * n / d) if d else 0

	n_trib = sum(n for k, _l, n in tribunal if k in ('SIN', 'DADAUN'))
	n_seid = seidauk.count()
	testu = {
		'mun': _('Munisípiu ho kazu barak liu: %(t)s.') % {'t': _top(mun, 3)} if mun else '',
		'tipu': _('Tipu kazu barak liu: %(t)s.') % {'t': _top(tipu, 2)} if tipu else '',
		'tinan': _('Tinan ho kazu rejistu barak liu: %(t)s.') % {'t': _top(sorted(tinan_lista, key=lambda x: -x[2]), 2)} if tinan_lista else '',
		'uma': _('Total uma-kain ida-ne\'e seidauk reprezenta kazu hotu: kazu %(n)s seidauk iha dadus uma-kain.') % {'n': laiha_uma} if laiha_uma else '',
		'tribunal': _('Husi kazu %(s)s ne\'ebé seidauk rezolve, %(n)s (%(p)s%%) rejistu ona ka rejistu hela iha tribunál.') % {'s': n_seid, 'n': n_trib, 'p': pct(n_trib, n_seid)} if n_seid else '',
		'la_trib': _('Tipu kazu barak liu ne\'ebé seidauk rejistu iha tribunál: %(t)s.') % {'t': _top(tipu_la_trib, 2)} if tipu_la_trib else '',
		'gov': _('Husi tipu kazu Governu foti komunidade nia rai (kazu %(n)s): uma-kain, mane, feto no labarik iha leten, maske dadus balu seidauk kompletu.') % {'n': gov.count()},
		'evik': _('Kazu %(n)s hetan eviksaun ona; uma-kain %(u)s afetadu.') % {'n': evik.count(), 'u': evik_af['uma_kain']},
	}
	n_evik = evik.count()
	frase = {
		'konsultasaun_molok': _('Kazu eviksaun %(n)s (%(p)s%%) la iha konsultasaun molok eviksaun.'),
		'notifikasaun_klaru': _('Kazu eviksaun %(n)s (%(p)s%%) la iha notifikasaun klaru molok eviksaun.'),
		'uza_forsa': _('Kazu eviksaun %(n)s (%(p)s%%) uza forsa durante eviksaun.'),
	}
	for c, lista in ev.items():
		n = sum(v for k, _l, v in lista if k == ('SIN' if c == 'uza_forsa' else 'LAE'))
		testu[c] = frase[c] % {'n': n, 'p': pct(n, n_evik)} if lista else ''
	naran_ev = {'konsultasaun_molok': _('Molok eviksaun halo konsultasaun?'), 'notifikasaun_klaru': _('Molok eviksaun iha notifikasaun?'),
		'uza_forsa': _('Durante eviksaun uza forsa?')}
	ev_tabela = [(naran_ev[c], *(sum(v for k, _l, v in lista if (k == x if x else k not in ('SIN', 'LAE'))) for x in ('SIN', 'LAE', None)))
		for c, lista in ev.items()]
	return {
		'total': total, 'afetadu': af, 'laiha_uma': laiha_uma, 'ev_tabela': ev_tabela,
		'n_tribunal': kazu.filter(segimentu__tribunal_rejistu='SIN').count(),
		'mun': mun, 'tipu': tipu, 'tinan': tinan_lista,
		'status': status, 'tribunal': tribunal, 'tipu_la_trib': tipu_la_trib, 'n_seidauk': n_seid,
		'gov_total': gov.count(), 'gov_af': gov_af, 'entidade': entidade,
		'evik_total': evik.count(), 'evik_af': evik_af, 'ev': ev,
		'testu': testu,
	}


def tabular(qs):
	"""Tabela kazu tuir munisípiu ho kolun grupu: tipu, status kazu, tribunál, eviksaun, populasaun."""
	kazu = _baze(qs)
	# Tipu ativu + tipu tuan ne'ebé kazu sira uza hela (la lakon husi tabela)
	tipus = list(TipuKonflitu.objects.filter(Q(is_active=True) | Q(pk__in=kazu.values('tipu_konflitu'))).distinct().order_by('-is_active', 'name'))
	kolun = [('total', 'total', Q())] + [('tipu', t.pk, Q(tipu_konflitu=t)) for t in tipus] + \
		[('rez', k, q) for k, _l, q in REZ_GRUPU] + [('trib', k, q) for k, _l, q in TRIB_GRUPU] + [('evik', k, q) for k, _l, q in EVIK_GRUPU]
	ann = {f'c{i}': Count('pk', filter=q, distinct=True) for i, (_g, _v, q) in enumerate(kolun)}
	por_mun = {r['munisipiu']: r for r in kazu.values('munisipiu').annotate(**ann)}
	tot_row = kazu.aggregate(**ann)
	pop = {r['kazu__munisipiu']: r for r in UmaKainAfetada.objects.filter(kazu__in=kazu).values('kazu__munisipiu')
		.annotate(uma=Sum('uma_kain'), ema=Sum('total_ema'))}
	pop_tot = UmaKainAfetada.objects.filter(kazu__in=kazu).aggregate(uma=Sum('uma_kain'), ema=Sum('total_ema'))
	rows = []
	for m in Munisipiu.active.all():
		r = por_mun.get(m.pk)
		if not r:
			continue
		rows.append({'mun': m, 'sel': [(g, v, r[f'c{i}']) for i, (g, v, _q) in enumerate(kolun)],
			'uma': (pop.get(m.pk) or {}).get('uma') or 0, 'ema': (pop.get(m.pk) or {}).get('ema') or 0})
	return {
		'tipus': tipus, 'rez': REZ_GRUPU, 'trib': TRIB_GRUPU, 'evik': EVIK_GRUPU, 'rows': rows,
		'total': [(g, v, tot_row[f'c{i}']) for i, (g, v, _q) in enumerate(kolun)],
		'uma': pop_tot['uma'] or 0, 'ema': pop_tot['ema'] or 0,
	}
