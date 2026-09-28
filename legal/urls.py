from django.urls import path
from legal.views import vault_v, kazu_v, nota_v

urlpatterns = [
	# Document Vault
	path('', vault_v.legalVault, name='legal-vault'),
	path('dokumentu/foun/', vault_v.DokumentuAdd, name='legal-dok-add'),
	path('dokumentu/<uuid:pk>/', vault_v.DokumentuDetail, name='legal-dok-detail'),
	path('dokumentu/<uuid:pk>/versaun/', vault_v.DokumentuVersaun, name='legal-dok-versaun'),
	path('dokumentu/<uuid:pk>/download/', vault_v.DokumentuDownload, name='legal-dok-download'),
	path('dokumentu/<uuid:pk>/arkivu/', vault_v.DokumentuArkivu, name='legal-dok-arkivu'),

	# Kazu legál
	path('kazu/', kazu_v.LegalKazuList, name='legal-kazu-list'),
	path('kazu/<uuid:uuid>/', kazu_v.LegalKazu, name='legal-kazu'),
	path('kazu/<uuid:uuid>/dossier/', kazu_v.LegalDossier, name='legal-dossier'),
	path('kazu/<uuid:uuid>/dokumentu/', vault_v.DokumentuAdd, name='legal-kazu-dok-add'),
	path('kazu/<uuid:uuid>/nota/', nota_v.NotaAdd, name='legal-nota-add'),
	path('nota/<int:pk>/edita/', nota_v.NotaUpdate, name='legal-nota-update'),
]
