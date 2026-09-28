from django.urls import path
from users.views import account_v
from . import views

urlpatterns = [
	path('', views.home, name='home'),
	path('login/', account_v.UserLoginView.as_view(), name='login'),
	path('logout/', account_v.UserLogoutView.as_view(), name='logout'),
	path('lian/', views.set_language, name='set-language'),
	path('manifest.json', views.manifest, name='manifest'),
	path('sw.js', views.service_worker, name='service-worker'),
	path('offline/', views.offline_page, name='offline-page'),
	path('media/<path:path>', views.protected_media, name='protected-media'),
]
