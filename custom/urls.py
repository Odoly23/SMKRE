from django.urls import path
from . import views

urlpatterns = [
	path('ajax/load-posts/', views.load_post, name='ajax_load_post'),
	path('ajax/load-suku/', views.load_suku, name='ajax_load_suku'),
	path('ajax/load-aldeia/', views.load_aldeia, name='ajax_load_aldeia'),
]
