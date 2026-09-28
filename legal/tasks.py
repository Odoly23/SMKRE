from datetime import timedelta
from celery import shared_task
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from config.rbac import OFISIAL_LEGAL
from legal.models import NotaLegal
from notification.utils import kirim_notif, kirim_notif_role

LOREN_LEMBRA = 3


@shared_task
def lembra_prazu():
	# Knaar kada loron (Celery Beat): prazu / audiénsia iha loron 3 tuir mai → lembrete ba Ofisiál Legál
	hoje = timezone.localdate()
	n = 0
	for nota in NotaLegal.objects.filter(remata=False, prazu__gte=hoje, prazu__lte=hoje + timedelta(days=LOREN_LEMBRA)).select_related('kazu', 'created_by'):
		loron = (nota.prazu - hoje).days
		msg = lambda nota=nota, loron=loron: _('Prazu %(tipu)s kazu %(kode)s: %(data)s (loron %(n)s tan).') % {
			'tipu': nota.get_tipu_display(), 'kode': nota.kazu.kode, 'data': nota.prazu.strftime('%d/%m/%Y'), 'n': loron}
		url = reverse('legal-kazu', args=[nota.kazu_id])
		kirim_notif_role([OFISIAL_LEGAL], 'LEGAL', msg, url=url, urgent=loron <= 1, email=True)
		if nota.created_by and nota.created_by.is_active and not nota.created_by.groups.filter(name=OFISIAL_LEGAL).exists():
			kirim_notif(nota.created_by, 'LEGAL', msg, url=url, urgent=loron <= 1, email=True)
		n += 1
	return {'lembra': n}
