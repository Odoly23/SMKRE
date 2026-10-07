from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import render
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_DASHBOARD
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import Evidensia, STATUS_CHOICES, STATUS_KAZU_CHOICES
from report.utils import report_queryset, STATUS_RELATORIU

MAPA_MAX_PIN = 3000
# Kór ikon kada status kazu (urjente = mean)
KOR_STATUS_KAZU = {'ABERTU': 'blue', 'INVESTIGASAUN': 'gold', 'AKSAUN_LEGAL': 'violet', 'TAKA': 'green'}


@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
def reportMapa(request):
	group = request.user.groups.all()[0].name
	status_label = dict(STATUS_CHOICES)
	kazu = report_queryset(request)

	# Pin kada kazu (iha GPS) + foto dahuluk ba popup
	mapobjects = kazu.exclude(latitude=None).select_related('munisipiu', 'postu', 'suku') \
		.prefetch_related('tipu_konflitu', 'afetadu',
			Prefetch('evidensia', queryset=Evidensia.objects.filter(tipu=Evidensia.FOTO).exclude(file=''), to_attr='fotos'))[:MAPA_MAX_PIN]

	# Hotspot: total kazu kada munisípiu (order_by(): Meta.ordering la tama iha GROUP BY)
	total = {r['munisipiu']: r['n'] for r in kazu.order_by().values('munisipiu').annotate(n=Count('id', distinct=True))}
	munobjects = [(m, total.get(m.pk, 0)) for m in Munisipiu.active.all()]

	context = {
		'group': group, "page": "mapa",
		'mapobjects': mapobjects, 'munobjects': munobjects,
		'status_kazu_list': [(code, label, KOR_STATUS_KAZU.get(code, 'grey')) for code, label in STATUS_KAZU_CHOICES],
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'status_list': [(s, status_label[s]) for s in STATUS_RELATORIU],
		'link_antes': [{'link_name': 'report-dash', 'link_text': _('Dashboard')}],
		'title': _('Mapa Konflitu Rai'), 'legend': _('Mapa Konflitu Rai — Timor-Leste')
	}
	return render(request, 'report/mapa.html', context)
