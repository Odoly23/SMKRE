from django.urls import path
from . import views

urlpatterns = [
	path('', views.NotificationList, name='notification-list'),
	path('<int:pk>/', views.NotificationOpen, name='notification-open'),
	path('lee-hotu/', views.NotificationReadAll, name='notification-read-all'),
]
