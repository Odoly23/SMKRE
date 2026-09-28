from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext as _
from custom.models import Munisipiu, TipuKonflitu
from publiku.models import Publikasaun
from publiku.services import limpa_filtru
from report.utils import chart_lang


def _portal_lang():
	# Testu ba portal.js (iha lian vizitante)
	return {
		'highcharts': chart_lang(),
		'kazu': _('kazu'), 'subar': _('Dadus subar ba privasidade'), 'klik': _('Klik atu filtra'),
		'klik_hamoos': _('Klik fali atu hamoos filtru'), 'mane': _('Mane'), 'feto': _('Feto'), 'labarik': _('Labarik'),
		'uma_kain': _('Uma-kain'), 'total': _('Total'), 'la_iha': _('La iha dadus'), 'suku': _('Kazu tuir suku'),
		'suku_hili': _('Hili munisípiu ida atu haree kazu tuir suku.'), 'munisipiu': _('Munisípiu'),
		'tipu': _('Tipu'), 'tinan': _('Tinan'), 'timor': 'Timor-Leste', 'legenda': _('Kazu kada munisípiu'),
		'ema': _('ema'), 'offline': _('Mapa baze (offline)'),
	}


def portalHome(request):
	# Portal públiku (la presiza login): mapa, gráfiku interativu, publikasaun, kontaktu
	context = {
		"page": "portal",
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'filtru': limpa_filtru(request.GET),
		'publikasaun': Publikasaun.objects.filter(status=Publikasaun.PUBLIKADU)[:6],
		'kontaktu': {'telefone': settings.PORTAL_TELEFONE, 'email': settings.PORTAL_EMAIL, 'enderesu': settings.PORTAL_ENDERESU},
		'limite': settings.PORTAL_LIMITE_SUBAR,
		'portal_lang': _portal_lang(),
		'title': 'Observatóriu Konflitu Rai',
	}
	return render(request, 'publiku/portal.html', context)


def publikasaunDownload(request, pk):
	# Publikadu: públiku. Rascunho: staf ho papél publikasaun deit (preview).
	obj = get_object_or_404(Publikasaun, pk=pk)
	if obj.status != Publikasaun.PUBLIKADU:
		from config.rbac import ROLE_POLICY_KRIA
		from users.auth_utils import c_user_group
		if not request.user.is_authenticated or c_user_group(request.user) not in ROLE_POLICY_KRIA:
			raise Http404
	try:
		f = obj.file.open('rb')
	except (FileNotFoundError, ValueError):
		raise Http404
	response = FileResponse(f, as_attachment=False, filename=f'{slugify(obj.titulu)[:60] or "publikasaun"}.pdf', content_type='application/pdf')
	response['X-Content-Type-Options'] = 'nosniff'
	return response
