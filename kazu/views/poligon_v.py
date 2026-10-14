import json
import logging
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from kazu.permissions import kazu_queryset, can_poligon
from kazu.poligon import rai_poligon

logger = logging.getLogger(__name__)
MAX_BYTES = 512 * 1024


@login_required
@require_POST
def KazuPoligon(request, uuid):
	# Rai poligon rai (GeoJSON husi Leaflet-Geoman). Server valida no kalkula fali luan (rumus Turf.js)
	kazu = get_object_or_404(kazu_queryset(request.user), pk=uuid)
	if not can_poligon(request.user, kazu):
		return JsonResponse({'erru': _('Ita la iha asesu atu edita poligon kazu ne\'e.')}, status=403)
	if len(request.body) > MAX_BYTES:
		return JsonResponse({'erru': _('Poligon boot liu.')}, status=400)
	try:
		data = json.loads(request.body or b'{}').get('poligon')
		rai_poligon(kazu, request.user, data)
	except (ValueError, AttributeError):
		return JsonResponse({'erru': _('Poligon la validu.')}, status=400)
	except ValidationError as e:
		return JsonResponse({'erru': ' '.join(e.messages)}, status=400)
	logger.info(f'Poligon kazu {kazu.kode or kazu.pk}: {kazu.poligon_luan_m2} m² husi {request.user.username}')
	return JsonResponse({
		'poligon': kazu.poligon, 'luan_m2': kazu.poligon_luan_m2, 'keliling_m': kazu.poligon_keliling_m,
		'rai_luan': kazu.rai_luan, 'rai_luan_unidade': kazu.get_rai_luan_unidade_display(),
	})
