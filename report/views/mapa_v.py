from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_DASHBOARD
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import STATUS_CHOICES
from report.utils import chart_lang, STATUS_RELATORIU


@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
def reportMapa(request):
	group = request.user.groups.all()[0].name
	status_label = dict(STATUS_CHOICES)
	context = {
		'group': group, "page": "mapa",
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'status_list': [(s, status_label[s]) for s in STATUS_RELATORIU],
		'chart_lang': chart_lang(),
		'title': _('Mapa Konflitu Rai'), 'legend': _('Mapa Konflitu Rai — Timor-Leste')
	}
	return render(request, 'report/mapa.html', context)
