from django.urls import path
from django.views.generic import RedirectView
from users.views import account_v
from . import views, views_hamoos

urlpatterns = [
	path('', views.home, name='home'),
	# Login staf: la iha link iha landing — staf hakerek /Tama-Lai/ rasik. /login/ la iha tan (404).
	path('Tama-Lai/', account_v.UserLoginView.as_view(), name='login'),
	path('tama-lai/', RedirectView.as_view(pattern_name='login', permanent=False)),
	path('logout/', account_v.UserLogoutView.as_view(), name='logout'),
	path('lian/', views.set_language, name='set-language'),
	path('manifest.json', views.manifest, name='manifest'),
	path('sw.js', views.service_worker, name='service-worker'),
	path('offline/', views.offline_page, name='offline-page'),
	path('media/<path:path>', views.protected_media, name='protected-media'),
	path('hamoos/<str:tipu>/<uuid:pk>/', views_hamoos.hamoos, name='hamoos'),     # Superadmin de'it
]
