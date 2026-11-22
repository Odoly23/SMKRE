from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext as _
from publiku.models import Publikasaun


# testu ba landing.js (iha lian vizitante)
def _portal_lang():
	return {
		'kazu': _('kazu'), 'atualiza': _('Atualiza'), 'dadus_ikus': _('Dadus ikus'), 'offline': _('Koneksaun lakon · dadus ikus'),
		'la_iha': _('La iha dadus'), 'tinan': _('Tinan'),
		'fatin_kazu': _('Fatin kazu'), 'naran_mun': _('Naran munisípiu'), 'munisipiu': _('Munisípiu'),
		'aproks': _('Fatin aproksimadu (~1 km)'),
		'loron': [_('Domingu'), _('Segunda'), _('Tersa'), _('Kuarta'), _('Kinta'), _('Sesta'), _('Sábadu')],
		'fulan': [_('Janeiru'), _('Fevereiru'), _('Marsu'), _('Abríl'), _('Maiu'), _('Juñu'), _('Jullu'), _('Agostu'),
			_('Setembru'), _('Outubru'), _('Novembru'), _('Dezembru')],
	}


# landing públiku (la presiza login): KPI, mapa, tendénsia, tipu, eviksaun — dadus hotu husi API públiku
def portalHome(request):
	context = {
		"page": "portal",
		'publikasaun': Publikasaun.objects.filter(status=Publikasaun.PUBLIKADU)[:6],
		'kontaktu': {'telefone': settings.PORTAL_TELEFONE, 'email': settings.PORTAL_EMAIL, 'enderesu': settings.PORTAL_ENDERESU},
		'limite': settings.PORTAL_LIMITE_SUBAR,
		'portal_lang': _portal_lang(),
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
