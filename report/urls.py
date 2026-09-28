from django.urls import path
from report.views import dash_v, mapa_v, export_v

urlpatterns = [
	path('dash/', dash_v.reportDash, name='report-dash'),
	path('grafiku/', dash_v.reportChart, name='report-chart'),
	path('mapa/', mapa_v.reportMapa, name='report-mapa'),

	# Lista (klik númeru iha dashboard)
	path('lista/', dash_v.rAllList, name='report-list'),
	path('lista/aktivu/', dash_v.rAktivuList, name='report-list-aktivu'),
	path('lista/urjente/', dash_v.rUrjenteList, name='report-list-urjente'),
	path('lista/status/<str:status>/', dash_v.rStatusList, name='report-status-list'),
	path('lista/tipu/<int:pk>/', dash_v.rTipuList, name='report-tipu-list'),
	path('lista/munisipiu/<int:pk>/', dash_v.rMunisipiuList, name='report-mun-list'),
	path('lista/tinan/<int:tinan>/', dash_v.rTinanList, name='report-tinan-list'),
	path('lista/investigador/<int:pk>/', dash_v.rStaffList, name='report-staff-list'),

	# Eksporta
	path('eksporta/excel/', export_v.exportExcel, name='report-export-excel'),
]
