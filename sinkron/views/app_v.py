from django.shortcuts import render
from django.utils import translation
from django.views.decorators.cache import cache_control


@cache_control(no_cache=True)
def sinkronApp(request):
	# App offline Investigadór. Pájina ne'e "kaskallu" deit (la iha dadus privadu), tan ne'e
	# service worker bele rai iha cache. Login liuhusi token JWT; dadus iha HP enkripta ho PIN.
	# App offline iha Tetun deit (tuir desizaun projetu).
	with translation.override('tet'):
		from kazu.models import KazuSegimentu, SIN_LAE_CHOICES
		opsaun = lambda c: [(k, str(v)) for k, v in KazuSegimentu._meta.get_field(c).choices]
		context = {
			"page": "sinkron",
			# Opsaun segimentu (tribunál, status, desizaun RbR) ba formuláriu offline
			'seg_ops': {'tribunal_rejistu': opsaun('tribunal_rejistu'), 'status_rezolusaun': opsaun('status_rezolusaun'),
				'desizaun_rbr': opsaun('desizaun_rbr'), 'sin_lae': [(k, str(v)) for k, v in SIN_LAE_CHOICES]},
			'title': 'Sinkron', 'legend': 'SIBAR-RbR Offline'
		}
		return render(request, 'sinkron/app.html', context)
