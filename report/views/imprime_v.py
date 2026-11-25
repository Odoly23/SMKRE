"""Lista kazu ba imprime (advokasia): A4 paizagem, kop Rede ba Rai, filtru hanesan Lista / Relatóriu.
Dadus advokasia de'it (la iha kontaktu pesoál). Máximu IMPRIME_MAX kazu — barak liu → uza Excel."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_RELATORIU
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import STATUS_CHOICES
from report.advokasia import kazu_eviksaun
from report.utils import report_queryset

IMPRIME_MAX = 1000


# testu filtru (ba títulu iha papél): munisípiu, tipu, status, tinan, buka
def _filtru_testu(g):
	parte = []
	if g.get('munisipiu'):
		m = Munisipiu.objects.filter(pk=g.get('munisipiu')).first()
		parte.append(_('Munisípiu: %(n)s') % {'n': m.name if m else '-'})
	if g.get('tipu'):
		t = TipuKonflitu.objects.filter(pk=g.get('tipu')).first()
		parte.append(_('Tipu: %(n)s') % {'n': t.name if t else '-'})
	if g.get('status'):
		parte.append(_('Status: %(n)s') % {'n': dict(STATUS_CHOICES).get(g.get('status'), g.get('status'))})
	if g.get('tinan'):
		parte.append(_('Tinan: %(n)s') % {'n': g.get('tinan')})
	if g.get('urjente'):
		parte.append(_('Urjente de\'it'))
	if g.get('q'):
		parte.append(_('Buka: "%(n)s"') % {'n': g.get('q')[:50]})
	return ' · '.join(parte) or _('Kazu hotu')


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def kazuImprime(request):
	kazu = report_queryset(request)
	total = kazu.count()
	evik = set(kazu_eviksaun(kazu).values_list('pk', flat=True))
	lista = kazu.select_related('munisipiu', 'postu', 'suku', 'segimentu').prefetch_related('tipu_konflitu', 'afetadu') \
		.order_by('munisipiu__name', 'data_relatoriu', 'kode')[:IMPRIME_MAX]
	linha, tot_uma, tot_ema = [], 0, 0
	for k in lista:
		seg = getattr(k, 'segimentu', None)
		uma, ema = k.total_uma_kain, k.total_afetadu
		tot_uma += uma
		tot_ema += ema
		linha.append({
			'k': k, 'uma': uma, 'ema': ema, 'evik': k.pk in evik,
			'tipu': ', '.join(t.name for t in k.tipu_konflitu.all()),
			'desizaun': seg.get_desizaun_rbr_display() if seg and seg.desizaun_rbr else '',
			'rezolusaun': seg.get_status_rezolusaun_display() if seg and seg.status_rezolusaun else '',
			'tribunal': seg.get_tribunal_rejistu_display() if seg and seg.tribunal_rejistu else '',
		})
	context = {
		'linha': linha, 'total': total, 'limite': IMPRIME_MAX, 'korta': total > IMPRIME_MAX,
		'tot_uma': tot_uma, 'tot_ema': tot_ema, 'tot_evik': sum(1 for x in linha if x['evik']),
		'filtru': _filtru_testu(request.GET), 'agora': timezone.localtime(),
		'husi': getattr(getattr(request.user, 'pesoaluser', None), 'pesoal', None) or request.user.username,
		'fila_query': request.GET.urlencode(),
	}
	return render(request, 'report/imprime.html', context)
