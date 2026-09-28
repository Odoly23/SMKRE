from django.shortcuts import render
from django.utils import translation
from django.views.decorators.cache import cache_control


@cache_control(no_cache=True)
def sinkronApp(request):
	# App offline Investigadór. Pájina ne'e "kaskallu" deit (la iha dadus privadu), tan ne'e
	# service worker bele rai iha cache. Login liuhusi token JWT; dadus iha HP enkripta ho PIN.
	# App offline iha Tetun deit (tuir desizaun projetu).
	with translation.override('tet'):
		context = {
			"page": "sinkron",
			'title': 'Sinkron', 'legend': 'SMKRE Offline'
		}
		return render(request, 'sinkron/app.html', context)
