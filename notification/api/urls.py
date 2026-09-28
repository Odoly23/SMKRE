from django.urls import path
from . import views

urlpatterns = [
	path('Notifikasaun/total/', views.APINotifTotal.as_view()),
	path('Notifikasaun/ikus/', views.APINotifLatest.as_view()),
]
