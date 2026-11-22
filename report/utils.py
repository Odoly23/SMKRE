"""Filtru no queryset ba relatóriu (fatin ida, uza iha views no api)."""
from kazu.models import DRAFT, ONGOING, PENDING, CANCELED, SYNCED, VERIFIED, APPROVED, COMPLETED
from kazu.permissions import kazu_queryset

# Relatóriu: kazu ne'ebé haruka ona ba server (la'ós rascunho iha HP, la'ós kanseladu)
STATUS_RELATORIU = [SYNCED, VERIFIED, APPROVED, 'REJECTED', COMPLETED, 'FOLLOWUP']
STATUS_AKTIVU = [SYNCED, VERIFIED, APPROVED, 'FOLLOWUP']
# Tipu kazu ne'ebé signifika eviksaun (komunidade hasai husi rai); DESLOKAMENTU = tipu tuan
TIPU_EVIKSAUN = ['GOV-RAI-ESTADU', 'GOV-RAI-ABANDONADU', 'DESLOKAMENTU']


# Q ba kazu eviksaun: tipu eviksaun, "Eviksaun akontese ona = Sin" ka iha insidente eviksaun
def filtru_eviksaun():
	from django.db.models import Q
	return Q(tipu_konflitu__code__in=TIPU_EVIKSAUN) | Q(eviksaun__eviksaun_akontese='SIN') | Q(insidente__isnull=False)


# kazu ba relatóriu (tuir papél utilizador) + filtru GET: munisipiu, tipu, status, tinan
def report_queryset(request):
	qs = kazu_queryset(request.user).exclude(status__in=[DRAFT, ONGOING, PENDING, CANCELED])
	g = request.GET
	if g.get('munisipiu'):
		qs = qs.filter(munisipiu_id=g.get('munisipiu'))
	if g.get('tipu'):
		qs = qs.filter(tipu_konflitu__id=g.get('tipu'))
	if g.get('status'):
		qs = qs.filter(status=g.get('status'))
	if g.get('tinan'):
		qs = qs.filter(data_relatoriu__year=g.get('tinan'))
	return qs.distinct()


# kazu eviksaun aktivu: status seidauk remata
def eviksaun_aktivu(qs):
	return qs.filter(status__in=STATUS_AKTIVU).filter(filtru_eviksaun()).distinct()


# testu Highcharts iha lian utilizador (json_script → smkre_charts.js)
def chart_lang():
	from django.utils.translation import gettext as _
	return {
		'loading': _('Karrega…'), 'noData': _('La iha dadus'),
		'contextButtonTitle': _('Menu gráfiku'), 'viewFullscreen': _('Haree ekran tomak'), 'exitFullscreen': _('Sai husi ekran tomak'),
		'printChart': _('Imprime gráfiku'), 'downloadPNG': _('Download PNG'), 'downloadJPEG': _('Download JPEG'),
		'downloadPDF': _('Download PDF'), 'downloadSVG': _('Download SVG'), 'downloadCSV': _('Download CSV'),
		'downloadXLS': _('Download Excel'), 'viewData': _('Haree tabela dadus'), 'hideData': _('Subar tabela dadus'),
		'thousandsSep': '.', 'decimalPoint': ',',
	}


# testu DataTables iha lian utilizador
def dt_lang():
	from django.utils.translation import gettext as _
	return {
		'search': _('Buka:'), 'lengthMenu': _('Hatudu _MENU_'), 'info': _('_START_–_END_ husi _TOTAL_'),
		'infoEmpty': _('La iha dadus'), 'infoFiltered': _('(filtra husi _MAX_)'), 'zeroRecords': _('La hetan dadus'),
		'emptyTable': _('La iha dadus'), 'paginate': {'first': '«', 'last': '»', 'next': '›', 'previous': '‹'},
	}


# tipu konflitu ba gráfiku / kontador: tipu ativu + tipu tuan (la ativu ona) ne'ebé kazu sira uza hela
# (la'ós ida ne'e → kazu ho tipu tuan la konta, gráfiku tipu mamuk)
def tipu_relatoriu(kazu):
	from django.db.models import Q
	from custom.models import TipuKonflitu
	uza = kazu.order_by().values_list('tipu_konflitu', flat=True).distinct()
	return TipuKonflitu.objects.filter(Q(is_active=True) | Q(pk__in=uza)).distinct().order_by('-is_active', 'name')
