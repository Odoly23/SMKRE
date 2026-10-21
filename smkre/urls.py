from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from report.views import live_v

urlpatterns = [
	path(settings.ADMIN_URL, admin.site.urls),
	path('', include('main.urls')),
	path('utilizador/', include('users.urls')),
	path('custom/', include('custom.urls')),
	path('notifikasaun/', include('notification.urls')),
	path('kazu/', include('kazu.urls')),
	path('report/', include('report.urls')),
	path('sinkron/', include('sinkron.urls')),
	path('legal/', include('legal.urls')),
	path('portal/', include('publiku.urls')),
	# Ekran Live (link privadu ba desktop all-in-one; la presiza login)
	path('live/<str:token>/', live_v.LiveKiosk, name='live-kiosk'),
	path('live/<str:token>/dadus/', live_v.LiveKioskDadus, name='live-kiosk-dadus'),

	# API
	path('api/notif/', include('notification.api.urls')),
	path('api/auth/', include('users.api.urls')),
	path('api/report/', include('report.api.urls')),
	path('api/sinkron/', include('sinkron.api.urls')),
	path('api/portal/', include('publiku.api.urls')),
]

handler403 = 'main.views.error_403'
handler404 = 'main.views.error_404'
handler500 = 'main.views.error_500'

admin.site.site_header = 'SIBAR-RbR — Administrasaun'
admin.site.site_title = 'SIBAR-RbR'
admin.site.index_title = 'Rede ba Rai'
