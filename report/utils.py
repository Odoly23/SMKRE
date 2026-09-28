"""Filtru no queryset ba relatóriu (fatin ida, uza iha views no api)."""
from kazu.models import DRAFT, ONGOING, PENDING, CANCELED, SYNCED, VERIFIED, APPROVED, COMPLETED
from kazu.permissions import kazu_queryset

# Relatóriu: kazu ne'ebé haruka ona ba server (la'ós rascunho iha HP, la'ós kanseladu)
STATUS_RELATORIU = [SYNCED, VERIFIED, APPROVED, 'REJECTED', COMPLETED]
STATUS_AKTIVU = [SYNCED, VERIFIED, APPROVED]
DESLOKAMENTU = 'DESLOKAMENTU'


def report_queryset(request):
	# Kazu ba relatóriu + filtru GET: munisipiu, tipu, status, tinan
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


def eviksaun_aktivu(qs):
	# Kazu eviksaun aktivu: tipu Deslokamentu Forsadu ka iha insidente eviksaun, status seidauk remata
	from django.db.models import Q
	return qs.filter(status__in=STATUS_AKTIVU).filter(Q(tipu_konflitu__code=DESLOKAMENTU) | Q(insidente__isnull=False)).distinct()


def chart_lang():
	# Testu Highcharts iha lian utilizador (json_script → smkre_charts.js)
	from django.utils.translation import gettext as _
	return {
		'loading': _('Karrega…'), 'noData': _('La iha dadus'),
		'contextButtonTitle': _('Menu gráfiku'), 'viewFullscreen': _('Haree ekran tomak'), 'exitFullscreen': _('Sai husi ekran tomak'),
		'printChart': _('Imprime gráfiku'), 'downloadPNG': _('Download PNG'), 'downloadJPEG': _('Download JPEG'),
		'downloadPDF': _('Download PDF'), 'downloadSVG': _('Download SVG'), 'downloadCSV': _('Download CSV'),
		'downloadXLS': _('Download Excel'), 'viewData': _('Haree tabela dadus'), 'hideData': _('Subar tabela dadus'),
		'thousandsSep': '.', 'decimalPoint': ',',
	}


def dt_lang():
	# Testu DataTables iha lian utilizador
	from django.utils.translation import gettext as _
	return {
		'search': _('Buka:'), 'lengthMenu': _('Hatudu _MENU_'), 'info': _('_START_–_END_ husi _TOTAL_'),
		'infoEmpty': _('La iha dadus'), 'infoFiltered': _('(filtra husi _MAX_)'), 'zeroRecords': _('La hetan dadus'),
		'emptyTable': _('La iha dadus'), 'paginate': {'first': '«', 'last': '»', 'next': '›', 'previous': '‹'},
	}
