from django.urls import path
from kazu.views import kazu_v, status_v, evidensia_v, import_v

urlpatterns = [
	path('', kazu_v.KazuList, name="kazu-list"),
	path('foun/', kazu_v.KazuAdd, name="kazu-add"),
	path('<uuid:uuid>/', kazu_v.KazuDetail, name="kazu-detail"),
	path('<uuid:uuid>/edita/', kazu_v.KazuUpdate, name="kazu-update"),
	path('<uuid:uuid>/evidensia/', evidensia_v.EvidensiaAdd, name="kazu-evidensia"),
	path('<uuid:uuid>/evidensia/<uuid:pk>/hamoos/', evidensia_v.EvidensiaDelete, name="kazu-evidensia-delete"),

	# Status (POST deit)
	# Import Excel (Admin)
	path('import/', import_v.KazuImportList, name="kazu-import"),
	path('import/template/', import_v.KazuImportTemplate, name="kazu-import-template"),
	path('import/<uuid:uuid>/', import_v.KazuImportDetail, name="kazu-import-detail"),
	path('import/<uuid:uuid>/konfirma/', import_v.KazuImportKonfirma, name="kazu-import-konfirma"),
	path('import/<uuid:uuid>/kansela/', import_v.KazuImportKansela, name="kazu-import-kansela"),
	path('<uuid:uuid>/lokasaun/', import_v.KazuLokasaun, name="kazu-lokasaun"),

	path('<uuid:uuid>/haruka/', status_v.KazuSubmit, name="kazu-submit"),
	path('<uuid:uuid>/status-kazu/', status_v.KazuStatusKazu, name="kazu-status-kazu"),
	path('<uuid:uuid>/<str:action>/', status_v.KazuAction, name="kazu-action"),
]
