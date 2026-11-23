"""Hamoos dadus permanente (Superadmin de'it). POST + konfirmasaun iha pájina (modal js-confirm)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_HAMOOS
from main import hamoos as H


# tipu → (modelu, kampu pk, funsaun hamoos, url detalla (erru), url lista (susesu))
def _tipu():
	from kazu.models import Kazu
	from legal.models import SurveiLegal, DokumentuLegal
	from publiku.models import Publikasaun
	from users.models import Pesoal
	return {
		'utilizador': (Pesoal, 'uuid', H.hamoos_utilizador, 'pesoal-detail', 'pesoal-list'),
		'kazu': (Kazu, 'pk', H.hamoos_kazu, 'kazu-detail', 'kazu-list'),
		'survei': (SurveiLegal, 'pk', H.hamoos_survei, 'legal-survei-detail', 'legal-survei-list'),
		'dokumentu': (DokumentuLegal, 'pk', H.hamoos_dokumentu, 'legal-dok-detail', 'legal-vault'),
		'publikasaun': (Publikasaun, 'pk', H.hamoos_publikasaun, 'publikasaun-update', 'publikasaun-list'),
	}


@login_required
@allowed_users(allowed_roles=ROLE_HAMOOS)
@require_POST
def hamoos(request, tipu, pk):
	t = _tipu().get(tipu)
	if not t:
		return redirect('home')
	Modelu, kampu, funsaun, url_detalla, url_lista = t
	obj = get_object_or_404(Modelu, **{kampu: pk})
	try:
		naran = funsaun(obj, request.user)
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
		kw = {'uuid': pk} if url_detalla in ('pesoal-detail', 'kazu-detail') else {'pk': pk}
		return redirect(url_detalla, **kw)
	messages.success(request, _('Hamoos ona: %(n)s') % {'n': naran})
	return redirect(url_lista)
