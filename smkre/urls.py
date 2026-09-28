from django.conf import settings
from django.contrib import admin
from django.urls import path, include

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

admin.site.site_header = 'SMKRE — Administrasaun'
admin.site.site_title = 'SMKRE'
admin.site.index_title = 'Rede ba Rai'
