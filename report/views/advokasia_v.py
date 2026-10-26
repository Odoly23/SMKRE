"""Lista kazu husi relatóriu tabular (klik númeru iha Dashboard)."""
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_RELATORIU
from custom.models import Munisipiu
from report import advokasia
from report.utils import report_queryset
from report.views.dash_v import _list


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def rTabularList(request, mun, grupu, valor):
	# mun=0: munisípiu hotu
	q = advokasia.filtru(grupu, valor)
	if q is None:
		raise Http404
	qs = report_queryset(request).filter(q)
	naran = _('Munisípiu hotu')
	if mun:
		m = get_object_or_404(Munisipiu, pk=mun)
		qs, naran = qs.filter(munisipiu=m), m.name
	return _list(request, qs.distinct(), f'{naran} · {advokasia.label_filtru(grupu, valor)}')
