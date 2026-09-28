from django.urls import path
from sinkron.views import app_v

urlpatterns = [
	path('', app_v.sinkronApp, name='sinkron'),
]
