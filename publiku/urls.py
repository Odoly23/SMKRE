from django.urls import path
from publiku.views import portal_v, publikasaun_v

urlpatterns = [
	# Públiku
	path('', portal_v.portalHome, name='portal'),
	path('publikasaun/<uuid:pk>/', portal_v.publikasaunDownload, name='portal-publikasaun'),

	# Staf: jere publikasaun
	path('jestaun/publikasaun/', publikasaun_v.PublikasaunList, name='publikasaun-list'),
	path('jestaun/publikasaun/foun/', publikasaun_v.PublikasaunAdd, name='publikasaun-add'),
	path('jestaun/publikasaun/<uuid:pk>/edita/', publikasaun_v.PublikasaunUpdate, name='publikasaun-update'),
	path('jestaun/publikasaun/<uuid:pk>/publika/', publikasaun_v.PublikasaunPublika, name='publikasaun-publika'),
]
