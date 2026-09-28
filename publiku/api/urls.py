from django.urls import path
from . import views

urlpatterns = [
	path('estatistika/', views.APIPortalEstatistika.as_view(), name='api-portal-estatistika'),
]
