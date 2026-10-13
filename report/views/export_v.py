import logging
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from config.decorators import allowed_users
from config.rbac import ROLE_RELATORIU
from report.utils import report_queryset

logger = logging.getLogger('smkre.seguransa')


# Kolun formuláriu RbR ba export — la inklui naran / kontaktu ema (privasidade)
SUBAR_EXPORT = {'portavos_naran', 'portavos_kontaktu', 'portavos_observasaun', 'fokal_naran', 'fokal_telemovel',
	'org_seluk_naran', 'org_seluk_kontaktu', 'advogadu_kontaktu'}


def _valor(obj, campo):
	# Valór ba Excel: label ba opsaun, data / númeru hanesan
	if obj is None:
		return ''
	f = obj._meta.get_field(campo)
	v = getattr(obj, campo)
	if f.choices:
		return str(getattr(obj, f'get_{campo}_display')()) if v else ''
	if v is None:
		return ''
	return float(v) if f.get_internal_type() == 'DecimalField' else v


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def exportExcel(request):
	# Eksporta kazu (tuir filtru) ba Excel. La inklui naran/kontaktu ema afetadu (privasidade).
	from kazu.importa import KAMPU_KAZU_RBR, KAMPU_SEGIMENTU
	from kazu.models import Kazu, KazuSegimentu
	kampu_kazu = [c for c in KAMPU_KAZU_RBR if c not in SUBAR_EXPORT]
	kampu_seg = [c for c in KAMPU_SEGIMENTU if c not in SUBAR_EXPORT]
	objects = report_queryset(request).select_related('munisipiu', 'postu', 'suku', 'aldeia', 'tipu_rai', 'created_by__pesoaluser__pesoal', 'segimentu') \
		.prefetch_related('tipu_konflitu', 'estragu', 'nesesidade', 'afetadu', 'insidente__tipu_eviksaun').order_by('kode')
	wb = Workbook()
	ws = wb.active
	ws.title = 'Kazu'
	head = [_('ID Kazu'), _('Naran kazu'), _('Data simu kazu iha RbR'), _('Data Akontesimentu'), _('Munisípiu'), _('Postu Administrativu'), _('Suku'), _('Aldeia'),
		_('Latitude'), _('Longitude'), _('Tipu Konflitu Rai'), _('Tipu Rai'), _('Status Dadus'), _('Status Kazu'), _('Urjente'),
		_('Uma-Kain'), _('Total Ema'), _('Mane'), _('Feto'), _('Labarik'), _('Katuas-Ferik'), _('Ema ho Defisiénsia'),
		_('Tipu Eviksaun'), _('Estragu Patrimóniu'), _('Nesesidade Urjente'), _('Investigadór')]
	head += [Kazu._meta.get_field(c).verbose_name for c in kampu_kazu] + [KazuSegimentu._meta.get_field(c).verbose_name for c in kampu_seg]
	ws.append([str(h) for h in head])
	for c in ws[1]:
		c.font = Font(bold=True, color='FFFFFF')
		c.fill = PatternFill('solid', fgColor='0E8A68')
		c.alignment = Alignment(vertical='center', wrap_text=True)
	for k in objects:
		af = list(k.afetadu.all())
		soma = lambda campo: sum(getattr(a, campo) or 0 for a in af)
		ws.append([
			k.kode or '', k.titulu, k.data_relatoriu, k.data_akontesimentu, k.munisipiu.name,
			k.postu.name if k.postu else '', k.suku.name if k.suku else '', k.aldeia.name if k.aldeia else '',
			float(k.latitude) if k.latitude is not None else None, float(k.longitude) if k.longitude is not None else None,
			', '.join(t.name for t in k.tipu_konflitu.all()), k.tipu_rai.name if k.tipu_rai else '',
			str(k.get_status_display()), str(k.get_status_kazu_display()), _('Sin') if k.urjente else _('Lae'),
			soma('uma_kain'), soma('total_ema'), soma('mane'), soma('feto'), soma('labarik'), soma('katuas_ferik'), soma('defisiensia'),
			', '.join(i.tipu_eviksaun.name for i in k.insidente.all()),
			', '.join(e.name for e in k.estragu.all()), ', '.join(n.name for n in k.nesesidade.all()),
			str(getattr(getattr(k.created_by, 'pesoaluser', None), 'pesoal', '') or k.created_by.username),
		] + [_valor(k, c) for c in kampu_kazu] + [_valor(getattr(k, 'segimentu', None) if hasattr(k, 'segimentu') else None, c) for c in kampu_seg])
	for i, _h in enumerate(head, start=1):
		ws.column_dimensions[get_column_letter(i)].width = 18
	ws.freeze_panes = 'A2'
	ws.auto_filter.ref = ws.dimensions
	buf = BytesIO()
	wb.save(buf)
	logger.info(f'Eksporta Excel: {objects.count()} kazu husi {request.user.username}')
	response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = f'attachment; filename="SIBAR-RbR-kazu-{timezone.localdate():%Y%m%d}.xlsx"'
	return response
