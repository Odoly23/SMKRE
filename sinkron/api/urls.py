from django.urls import path
from . import views

urlpatterns = [
	path('opsaun/', views.APIOpsaun.as_view(), name='api-sinkron-opsaun'),
	path('kazu/', views.APIKazuLista.as_view(), name='api-sinkron-kazu'),
	path('kazu/<uuid:uuid>/evidensia/', views.APIEvidensia.as_view(), name='api-sinkron-evidensia'),
	path('kazu/<uuid:uuid>/haruka/', views.APIHaruka.as_view(), name='api-sinkron-haruka'),
]
