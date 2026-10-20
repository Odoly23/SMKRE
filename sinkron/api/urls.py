from django.urls import path
from . import views

urlpatterns = [
	path('opsaun/', views.APIOpsaun.as_view(), name='api-sinkron-opsaun'),
	path('kazu/', views.APIKazuLista.as_view(), name='api-sinkron-kazu'),
	path('kazu/<uuid:uuid>/evidensia/', views.APIEvidensia.as_view(), name='api-sinkron-evidensia'),
	path('kazu/<uuid:uuid>/haruka/', views.APIHaruka.as_view(), name='api-sinkron-haruka'),
	path('kazu/<uuid:uuid>/followup/', views.APIFollowup.as_view(), name='api-sinkron-followup'),
	# Survei legál (Ofisiál Legál)
	path('legal/opsaun/', views.APIOpsaunLegal.as_view(), name='api-sinkron-legal-opsaun'),
	path('legal/survei/', views.APISurveiLista.as_view(), name='api-sinkron-survei'),
	path('legal/survei/<uuid:uuid>/file/', views.APISurveiFile.as_view(), name='api-sinkron-survei-file'),
	path('legal/survei/<uuid:uuid>/haruka/', views.APISurveiHaruka.as_view(), name='api-sinkron-survei-haruka'),
]
