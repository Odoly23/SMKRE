"""Dashboard legál: KPI, gráfiku, mapa, prazu & tarefa."""
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, IntegerField
from django.db.models.functions import Coalesce, ExtractYear
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_LEGAL, ROLE_SURVEI_HAREE, OFISIAL_LEGAL
from custom.models import Munisipiu
from kazu.models import Kazu, KazuSegimentu, AKSAUN_LEGAL
from legal.models import NotaLegal, SurveiLegal
from legal.services import dokumentu_queryset, can_edit_vault, KAZU_STATUS_LEGAL
from legal.tasks import LOREN_LEMBRA
from report.advokasia import tribunal_rezumu
from report.utils import chart_lang, report_queryset
from users.auth_utils import c_user_group
from users.models import OfflinePermission


def _seri(qs, campo, choices):
	n = dict(qs.values_list(campo).annotate(n=Count('pk')).values_list(campo, 'n'))
	return {'label': [str(l) for c, l in choices], 'obj': [n.get(c, 0) for c, l in choices]}


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL)
def LegalDash(request):
	hoje = timezone.localdate()
	group = c_user_group(request.user)
	kazu = Kazu.objects.filter(status__in=KAZU_STATUS_LEGAL)
	legal = kazu.filter(status_kazu=AKSAUN_LEGAL)
	nota = NotaLegal.objects.filter(kazu__in=kazu, remata=False).select_related('kazu')
	if not can_edit_vault(request.user):
		nota = nota.filter(konfidensial=False)
	haree_survei = group in ROLE_SURVEI_HAREE
	survei = SurveiLegal.objects.exclude(status=SurveiLegal.RASCUNHO) if haree_survei else SurveiLegal.objects.none()

	# Tribunál / rezolusaun: regra IDA ho Dashboard Relatóriu no Gráfiku (kazu hotu ne'ebé haruka ona)
	baze = report_queryset(request)
	trib = tribunal_rezumu(baze)
	seg = KazuSegimentu.objects.filter(kazu__in=baze.values('pk'))
	kpi = {
		'legal': legal.count(),
		'tribunal': trib['rejistu'],
		'desizaun': trib['desizaun'],
		'prazu': nota.filter(prazu__gte=hoje, prazu__lte=hoje + timedelta(days=7)).count(),
		'liu_prazu': nota.filter(prazu__lt=hoje).count(),
		'dokumentu': dokumentu_queryset(request.user).count(),
		'survei': survei.count(),
		'survei_hein': survei.filter(status=SurveiLegal.HARUKA).count(),
	}

	# Gráfiku
	mun = Munisipiu.active.all()
	n_mun = dict(legal.values_list('munisipiu').annotate(n=Count('pk')).values_list('munisipiu', 'n'))
	n_survei = dict(survei.values_list('munisipiu').annotate(n=Count('pk')).values_list('munisipiu', 'n'))
	tinan = legal.annotate(t=Coalesce(ExtractYear('data_relatoriu'), 'tinan_simu', output_field=IntegerField())).exclude(t=None) \
		.values_list('t').annotate(n=Count('pk')).order_by('t')
	charts = {
		'mun': {'label': [m.name for m in mun], 'kazu': [n_mun.get(m.pk, 0) for m in mun], 'survei': [n_survei.get(m.pk, 0) for m in mun]},
		'tribunal': {'label': [str(l) for _k, l, _n in trib['tribunal']], 'obj': [n for _k, _l, n in trib['tribunal']]},
		'desizaun': _seri(seg, 'desizaun_rbr', KazuSegimentu.DESIZAUN_RBR_CHOICES),
		'rezolusaun': {'label': [str(l) for _k, l, _n in trib['rezolusaun']], 'obj': [n for _k, _l, n in trib['rezolusaun']]},
		'tinan': {'label': [str(t) for t, n in tinan], 'obj': [n for t, n in tinan]},
		'meius': _seri(survei, 'meius', SurveiLegal.MEIUS_CHOICES),
		'labels': {'kazu': _('Kazu legál'), 'survei': _('Survei legál'), 'total': _('Total')},
	}

	# Mapa: kazu iha prosesu legál + survei legál ho GPS
	pontu = [{'lat': float(k.latitude), 'lng': float(k.longitude), 't': 'kazu', 'kode': k.kode or '',
		'fatin': ', '.join(str(x) for x in (k.suku, k.munisipiu) if x), 'url': reverse('legal-kazu', args=[k.pk])}
		for k in legal.exclude(latitude=None).exclude(longitude=None).select_related('suku', 'munisipiu')[:2000]]
	pontu += [{'lat': float(s.latitude), 'lng': float(s.longitude), 't': 'survei', 'kode': s.kode or '',
		'fatin': ', '.join(str(x) for x in (s.suku, s.munisipiu) if x), 'url': reverse('legal-survei-detail', args=[s.pk])}
		for s in survei.exclude(latitude=None).exclude(longitude=None).select_related('suku', 'munisipiu')[:2000]]

	# Prazu & tarefa
	prazu = nota.exclude(prazu=None).filter(prazu__lte=hoje + timedelta(days=30)).order_by('prazu')[:15]
	context = {
		"page": "legal", 'kpi': kpi, 'charts': charts, 'pontu': pontu, 'prazu': prazu, 'hoje': hoje,
		'limite': hoje + timedelta(days=LOREN_LEMBRA), 'haree_survei': haree_survei,
		'survei_hein': survei.filter(status=SurveiLegal.HARUKA).select_related('munisipiu')[:8],
		'survei_foun': SurveiLegal.objects.filter(created_by=request.user).exclude(status=SurveiLegal.VERIFIKADU)[:8]
			if group == OFISIAL_LEGAL else [],
		'ofisial_ativu': User.objects.filter(groups__name=OFISIAL_LEGAL, offline_permission__in=OfflinePermission.objects.valid())
			.select_related('pesoaluser__pesoal').distinct() if haree_survei else [],
		'chart_lang': chart_lang(),
		'title': _('Dashboard Legál'), 'legend': _('Dashboard Legál')
	}
	return render(request, 'legal/dash.html', context)
