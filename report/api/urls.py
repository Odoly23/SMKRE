from django.urls import path
from . import views

urlpatterns = [
	path('kazu/mun/', views.APIKazuMun.as_view()),
	path('kazu/tipu/', views.APIKazuTipu.as_view()),
	path('kazu/status/', views.APIKazuStatus.as_view()),
	path('kazu/tendensia/', views.APIKazuTendensia.as_view()),
	path('kazu/afetadu/', views.APIAfetadu.as_view()),
	path('kazu/mapa/', views.APIMapa.as_view()),
]
