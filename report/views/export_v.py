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


@login_required
@allowed_users(allowed_roles=ROLE_RELATORIU)
def exportExcel(request):
	# Eksporta kazu (tuir filtru) ba Excel. La inklui naran/kontaktu ema afetadu (privasidade).
	objects = report_queryset(request).select_related('munisipiu', 'postu', 'suku', 'aldeia', 'tipu_rai', 'created_by__pesoaluser__pesoal') \
		.prefetch_related('tipu_konflitu', 'estragu', 'nesesidade', 'afetadu', 'insidente__tipu_eviksaun').order_by('kode')
	wb = Workbook()
	ws = wb.active
	ws.title = 'Kazu'
	head = [_('ID Kazu'), _('Data Relatóriu'), _('Data Akontesimentu'), _('Munisípiu'), _('Postu Administrativu'), _('Suku'), _('Aldeia'),
		_('Latitude'), _('Longitude'), _('Tipu Konflitu Rai'), _('Tipu Rai'), _('Status Dadus'), _('Status Kazu'), _('Urjente'),
		_('Uma-Kain'), _('Total Ema'), _('Mane'), _('Feto'), _('Labarik'), _('Katuas-Ferik'), _('Ema ho Defisiénsia'),
		_('Tipu Eviksaun'), _('Estragu Patrimóniu'), _('Nesesidade Urjente'), _('Investigadór')]
	ws.append([str(h) for h in head])
	for c in ws[1]:
		c.font = Font(bold=True, color='FFFFFF')
		c.fill = PatternFill('solid', fgColor='0E8A68')
		c.alignment = Alignment(vertical='center', wrap_text=True)
	for k in objects:
		af = list(k.afetadu.all())
		soma = lambda campo: sum(getattr(a, campo) or 0 for a in af)
		ws.append([
			k.kode or '', k.data_relatoriu, k.data_akontesimentu, k.munisipiu.name,
			k.postu.name if k.postu else '', k.suku.name if k.suku else '', k.aldeia.name if k.aldeia else '',
			float(k.latitude) if k.latitude is not None else None, float(k.longitude) if k.longitude is not None else None,
			', '.join(t.name for t in k.tipu_konflitu.all()), k.tipu_rai.name if k.tipu_rai else '',
			str(k.get_status_display()), str(k.get_status_kazu_display()), _('Sin') if k.urjente else _('Lae'),
			soma('uma_kain'), soma('total_ema'), soma('mane'), soma('feto'), soma('labarik'), soma('katuas_ferik'), soma('defisiensia'),
			', '.join(i.tipu_eviksaun.name for i in k.insidente.all()),
			', '.join(e.name for e in k.estragu.all()), ', '.join(n.name for n in k.nesesidade.all()),
			str(getattr(getattr(k.created_by, 'pesoaluser', None), 'pesoal', '') or k.created_by.username),
		])
	for i, _h in enumerate(head, start=1):
		ws.column_dimensions[get_column_letter(i)].width = 18
	ws.freeze_panes = 'A2'
	ws.auto_filter.ref = ws.dimensions
	buf = BytesIO()
	wb.save(buf)
	logger.info(f'Eksporta Excel: {objects.count()} kazu husi {request.user.username}')
	response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = f'attachment; filename="SMKRE-kazu-{timezone.localdate():%Y%m%d}.xlsx"'
	return response
