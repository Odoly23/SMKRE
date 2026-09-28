from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_DASHBOARD, ROLE_RELATORIU, INVESTIGADOR
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import UmaKainAfetada, STATUS_CHOICES, COMPLETED
from report.utils import chart_lang, dt_lang, report_queryset, eviksaun_aktivu, STATUS_RELATORIU


@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
def reportDash(request):
	group = request.user.groups.all()[0].name
	objects1, objects2, objects3, objects4, objects5, objects6 = [], [], [], [], [], []
	kazu = report_queryset(request)
	total = kazu.count()
	tot_aktivu = eviksaun_aktivu(kazu).count()
	afetadu = UmaKainAfetada.objects.filter(kazu__in=kazu)
	tot_uma_kain = afetadu.aggregate(t=Sum('uma_kain'))['t'] or 0
	tot_remata = kazu.filter(status=COMPLETED).count()
	tot_urjente = kazu.filter(urjente=True).exclude(status=COMPLETED).count()
	status_label = dict(STATUS_CHOICES)
	for s in STATUS_RELATORIU:
		r1 = kazu.filter(status=s).count()
		objects1.append([s, status_label[s], r1])
	tipus = TipuKonflitu.active.all()
	for t in tipus:
		r2 = kazu.filter(tipu_konflitu=t).count()
		objects2.append([t, r2])
	muns = Munisipiu.active.all()
	for m in muns:
		r3 = kazu.filter(munisipiu=m).count()
		objects3.append([m, r3])
	tinan = sorted({d.year for d in kazu.exclude(data_relatoriu=None).values_list('data_relatoriu', flat=True)}, reverse=True)
	for y in tinan:
		r4 = kazu.filter(data_relatoriu__year=y).count()
		objects4.append([y, r4])
	for m in muns:
		r5 = afetadu.filter(kazu__munisipiu=m).aggregate(
			uma_kain=Sum('uma_kain'), total=Sum('total_ema'), mane=Sum('mane'), feto=Sum('feto'),
			labarik=Sum('labarik'), katuas=Sum('katuas_ferik'), defisiensia=Sum('defisiensia'))
		if any(r5.values()):
			objects5.append([m, r5])
	staff = User.objects.filter(groups__name=INVESTIGADOR).select_related('pesoaluser__pesoal')
	for u in staff:
		r6 = kazu.filter(created_by=u).count()
		if r6:
			objects6.append([u, r6])
	context = {
		'group': group, "page": "dashboard",
		'total': total, 'tot_aktivu': tot_aktivu, 'tot_uma_kain': tot_uma_kain, 'tot_remata': tot_remata, 'tot_urjente': tot_urjente,
		'objects1': objects1, 'objects2': objects2, 'objects3': objects3,
		'objects4': objects4, 'objects5': objects5, 'objects6': objects6,
		'munisipiu_list': muns, 'tipu_list': tipus,
		'title': _('Dashboard Relatóriu'), 'legend': _('Dashboard Relatóriu')
	}
	return render(request, 'report/dash.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
def reportChart(request):
	group = request.user.groups.all()[0].name
	context = {
		'group': group, "page": "dashboard",
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'title': _('Gráfiku'), 'legend': _('Gráfiku no Tendénsia'),
		'chart_lang': chart_lang(),
	}
	return render(request, 'report/chart_dash.html', context)


# ══════════════ LISTA (klik númeru iha dashboard) ══════════════

def _list(request, objects, legend, template='report/list.html'):
	group = request.user.groups.all()[0].name
	objects = objects.select_related('munisipiu', 'postu', 'suku', 'created_by__pesoaluser__pesoal') \
		.prefetch_related('tipu_konflitu', 'afetadu').order_by('-data_relatoriu')
	context = {
		'group': group, "page": "relatoriu",
		'objects': objects, 'title': legend, 'legend': legend,
		'export_query': request.GET.urlencode(), 'dt_lang': dt_lang(),
	}
	return render(request, template, context)


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rAllList(request):
	return _list(request, report_queryset(request), _('Lista Kazu Hotu'))


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rAktivuList(request):
	return _list(request, eviksaun_aktivu(report_queryset(request)), _('Lista Kazu Eviksaun Aktivu'))


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rUrjenteList(request):
	return _list(request, report_queryset(request).filter(urjente=True).exclude(status=COMPLETED), _('Lista Kazu Urjente'))


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rStatusList(request, status):
	label = dict(STATUS_CHOICES).get(status, status)
	return _list(request, report_queryset(request).filter(status=status), _('Lista Kazu Status %(s)s') % {'s': label})


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rTipuList(request, pk):
	obj = get_object_or_404(TipuKonflitu, pk=pk)
	return _list(request, report_queryset(request).filter(tipu_konflitu=obj), _('Lista Kazu Tipu %(s)s') % {'s': obj.name})


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rMunisipiuList(request, pk):
	obj = get_object_or_404(Munisipiu, pk=pk)
	return _list(request, report_queryset(request).filter(munisipiu=obj), _('Lista Kazu Munisípiu %(s)s') % {'s': obj.name})


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rTinanList(request, tinan):
	return _list(request, report_queryset(request).filter(data_relatoriu__year=tinan), _('Lista Kazu Tinan %(s)s') % {'s': tinan})


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rStaffList(request, pk):
	obj = get_object_or_404(User, pk=pk, groups__name=INVESTIGADOR)
	naran = getattr(getattr(obj, 'pesoaluser', None), 'pesoal', None) or obj.username
	return _list(request, report_queryset(request).filter(created_by=obj), _('Lista Kazu Investigadór %(s)s') % {'s': naran})
