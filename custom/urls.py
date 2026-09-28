from django.urls import path
from . import views

urlpatterns = [
	path('ajax/postu/', views.load_postu, name='ajax-load-postu'),
	path('ajax/suku/', views.load_suku, name='ajax-load-suku'),
	path('ajax/aldeia/', views.load_aldeia, name='ajax-load-aldeia'),
]
