import hashlib
from django.contrib.auth.decorators import login_required
from config.paginasaun import pajina
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Sum, Count
from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_DASHBOARD, ROLE_RELATORIU, ROLE_INPUT_KAZU
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import UmaKainAfetada, STATUS_CHOICES, COMPLETED
from report import advokasia
from report.utils import chart_lang, report_queryset, eviksaun_aktivu, tipu_relatoriu, STATUS_RELATORIU

# Tempu cache ba dashboard/gráfiku (segundu): HP barak ka refresh beibeik la todan server.
CACHE_SEG = 60


# chave cache tuir utilizador (kazu ne'ebé nia bele haree) no filtru GET
def _chave_cache(prefix, request):
	bruto = f'{request.user.pk}:{request.GET.urlencode()}'
	return f'{prefix}:{hashlib.md5(bruto.encode()).hexdigest()}'


# kalkula dadus todan dashboard (query GROUP BY) — rezultadu rai iha cache
def _kalkula_dash(request):
	objects1, objects2, objects3, objects4, objects5, objects6 = [], [], [], [], [], []
	kazu = report_queryset(request)
	total = kazu.count()
	tot_aktivu = eviksaun_aktivu(kazu).count()
	afetadu = UmaKainAfetada.objects.filter(kazu__in=kazu)
	tot_uma_kain = afetadu.aggregate(t=Sum('uma_kain'))['t'] or 0
	tot_remata = kazu.filter(status=COMPLETED).count()
	tot_urjente = kazu.filter(urjente=True).exclude(status=COMPLETED).count()
	# Kada grupu = QUERY IDA (GROUP BY), la'ós loop filter-count (evita query ×N).
	# .order_by() mamuk: hamoos ordem default (Meta) atu la tama iha GROUP BY no fahe grupu.
	status_label = dict(STATUS_CHOICES)
	n_status = dict(kazu.order_by().values_list('status').annotate(n=Count('pk', distinct=True)).values_list('status', 'n'))
	for s in STATUS_RELATORIU:
		objects1.append([s, status_label[s], n_status.get(s, 0)])
	n_tipu = dict(kazu.order_by().values_list('tipu_konflitu').annotate(n=Count('pk', distinct=True)).values_list('tipu_konflitu', 'n'))
	for t in tipu_relatoriu(kazu):
		objects2.append([t, n_tipu.get(t.pk, 0)])
	n_mun = dict(kazu.order_by().values_list('munisipiu').annotate(n=Count('pk', distinct=True)).values_list('munisipiu', 'n'))
	muns = Munisipiu.active.all()
	for m in muns:
		objects3.append([m, n_mun.get(m.pk, 0)])
	n_tinan = kazu.order_by().exclude(data_relatoriu=None).annotate(y=ExtractYear('data_relatoriu')).values_list('y').annotate(n=Count('pk', distinct=True))
	for y, n in sorted(n_tinan, reverse=True):
		objects4.append([y, n])
	afe_mun = {r['kazu__munisipiu']: r for r in afetadu.order_by().values('kazu__munisipiu').annotate(
		uma_kain=Sum('uma_kain'), total=Sum('total_ema'), mane=Sum('mane'), feto=Sum('feto'),
		labarik=Sum('labarik'), katuas=Sum('katuas_ferik'), defisiensia=Sum('defisiensia'))}
	for m in muns:
		r5 = afe_mun.get(m.pk)
		if r5 and any(v for k, v in r5.items() if k != 'kazu__munisipiu'):
			objects5.append([m, r5])
	n_staff = dict(kazu.order_by().values_list('created_by').annotate(n=Count('pk', distinct=True)).values_list('created_by', 'n'))
	staff = User.objects.filter(groups__name__in=ROLE_INPUT_KAZU).distinct().select_related('pesoaluser__pesoal')
	for u in staff:
		if n_staff.get(u.pk):
			objects6.append([u, n_staff[u.pk]])
	return {
		'total': total, 'tot_aktivu': tot_aktivu, 'tot_uma_kain': tot_uma_kain, 'tot_remata': tot_remata, 'tot_urjente': tot_urjente,
		'objects1': objects1, 'objects2': objects2, 'objects3': objects3,
		'objects4': objects4, 'objects5': objects5, 'objects6': objects6,
		'adv': advokasia.advokasia(kazu), 't': advokasia.tabular(kazu),     # status kazu, tribunál, eviksaun, Governu foti rai + tabela munisípiu
	}


# hare dashboard relatóriu (totál, status, tipu, munisípiu, tinan, afetadu, staff)
@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
def reportDash(request):
	chave = _chave_cache('report-dash', request)
	dados = cache.get(chave)
	if dados is None:
		dados = _kalkula_dash(request)
		cache.set(chave, dados, CACHE_SEG)
	context = {
		'group': request.user.groups.all()[0].name, "page": "dashboard",
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'title': _('Dashboard Relatóriu'), 'legend': _('Dashboard Relatóriu'),
		**dados,
	}
	return render(request, 'report/dash.html', context)


# dadus ba gráfiku advokasia (status kazu, tribunál, Governu foti rai, eviksaun) + testu rezumu
def _graf_advokasia(d):
	par = lambda lista: [[str(l), n] for _k, l, n in lista]
	return {
		'tinan': par(d['tinan']), 'status': par(d['status']), 'tribunal': par(d['tribunal']),
		'tipu_la_trib': par(d['tipu_la_trib']), 'entidade': par(d['entidade']),
		**{c: par(lista) for c, lista in d['ev'].items()},
		'testu': {k: str(v) for k, v in d['testu'].items()},
	}


# hare gráfiku no tendénsia (dadus advokasia iha cache)
@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
def reportChart(request):
	chave = _chave_cache('report-chart', request)
	graf = cache.get(chave)
	if graf is None:
		graf = _graf_advokasia(advokasia.advokasia(report_queryset(request)))
		cache.set(chave, graf, CACHE_SEG)
	context = {
		'group': request.user.groups.all()[0].name, "page": "grafiku",
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'title': _('Gráfiku'), 'legend': _('Gráfiku no Tendénsia'),
		'chart_lang': chart_lang(), 'graf': graf,
	}
	return render(request, 'report/chart_dash.html', context)


# ══════════════ LISTA (klik númeru iha dashboard) ══════════════

# baze lista kazu (klik númeru iha dashboard): pájina 10 (server) + link "Excel kompletu"
def _list(request, objects, legend, template='report/list.html'):
	group = request.user.groups.all()[0].name
	objects = objects.select_related('munisipiu', 'postu', 'suku', 'segimentu', 'created_by__pesoaluser__pesoal') \
		.prefetch_related('tipu_konflitu', 'afetadu').order_by('-created_at', '-pk')
	# Pájina 10 (server): kmaan ba HP; "Excel kompletu" exporta dadus hotu ho filtru hanesan
	q = request.GET.copy()
	q.pop('page', None)
	context = {
		'group': group, "page": "relatoriu",
		'objects': pajina(request, objects), 'title': legend, 'legend': legend,
		'export_query': q.urlencode(),
	}
	return render(request, template, context)


# lista kazu hotu (tuir filtru)
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rAllList(request):
	return _list(request, report_queryset(request), _('Lista Kazu Hotu'))


# lista kazu eviksaun aktivu (status seidauk remata)
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rAktivuList(request):
	return _list(request, eviksaun_aktivu(report_queryset(request)), _('Lista Kazu Eviksaun Aktivu'))


# lista kazu urjente (la'ós remata)
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rUrjenteList(request):
	return _list(request, report_queryset(request).filter(urjente=True).exclude(status=COMPLETED), _('Lista Kazu Urjente'))


# lista kazu tuir status ida
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rStatusList(request, status):
	label = dict(STATUS_CHOICES).get(status, status)
	return _list(request, report_queryset(request).filter(status=status), _('Lista Kazu Status %(s)s') % {'s': label})


# lista kazu tuir tipu konflitu
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rTipuList(request, pk):
	obj = get_object_or_404(TipuKonflitu, pk=pk)
	return _list(request, report_queryset(request).filter(tipu_konflitu=obj), _('Lista Kazu Tipu %(s)s') % {'s': obj.name})


# lista kazu tuir munisípiu
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rMunisipiuList(request, pk):
	obj = get_object_or_404(Munisipiu, pk=pk)
	return _list(request, report_queryset(request).filter(munisipiu=obj), _('Lista Kazu Munisípiu %(s)s') % {'s': obj.name})


# lista kazu tuir tinan (data relatóriu)
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rTinanList(request, tinan):
	return _list(request, report_queryset(request).filter(data_relatoriu__year=tinan), _('Lista Kazu Tinan %(s)s') % {'s': tinan})


# lista kazu tuir investigadór (sira mak kria)
@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rStaffList(request, pk):
	obj = get_object_or_404(User.objects.filter(groups__name__in=ROLE_INPUT_KAZU).distinct(), pk=pk)
	naran = getattr(getattr(obj, 'pesoaluser', None), 'pesoal', None) or obj.username
	return _list(request, report_queryset(request).filter(created_by=obj), _('Lista Kazu Investigadór %(s)s') % {'s': naran})
