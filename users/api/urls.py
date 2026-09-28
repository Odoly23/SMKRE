from django.urls import path
from . import views

urlpatterns = [
	path('token/', views.APIOfflineTokenObtain.as_view(), name='api-token'),
	path('token/refresh/', views.APIOfflineTokenRefresh.as_view(), name='api-token-refresh'),
	path('me/', views.APIMe.as_view(), name='api-me'),
]
