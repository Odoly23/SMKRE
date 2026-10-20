from django.urls import path
from legal.views import vault_v, kazu_v, nota_v, survei_v, dash_v, autorizasaun_v

urlpatterns = [
	# Dashboard legál
	path('dashboard/', dash_v.LegalDash, name='legal-dash'),

	# Ativa input legál (Admin / Superadmin hili Ofisiál Legál + data)
	path('autorizasaun/', autorizasaun_v.AutorizasaunLegal, name='legal-autorizasaun'),
	path('autorizasaun/<int:pk>/renova/', autorizasaun_v.AutorizasaunRenova, name='legal-autorizasaun-renova'),
	path('autorizasaun/<int:pk>/kansela/', autorizasaun_v.AutorizasaunKansela, name='legal-autorizasaun-kansela'),

	# Survei legál (Perguntas Xave Sira Legal)
	path('survei/', survei_v.SurveiList, name='legal-survei-list'),
	path('survei/foun/', survei_v.SurveiAdd, name='legal-survei-add'),
	path('survei/<uuid:pk>/', survei_v.SurveiDetail, name='legal-survei-detail'),
	path('survei/<uuid:pk>/pdf/', survei_v.SurveiPDF, name='legal-survei-pdf'),
	path('survei/<uuid:pk>/edita/', survei_v.SurveiUpdate, name='legal-survei-update'),
	path('survei/<uuid:pk>/haruka/', survei_v.SurveiHaruka, name='legal-survei-haruka'),
	path('survei/<uuid:pk>/verifika/', survei_v.SurveiVerifika, name='legal-survei-verifika'),
	path('survei/<uuid:pk>/file/', survei_v.SurveiFileAdd, name='legal-survei-file-add'),
	path('survei/file/<uuid:pk>/', survei_v.SurveiFileDownload, name='legal-survei-file'),
	path('survei/file/<uuid:pk>/hamoos/', survei_v.SurveiFileDelete, name='legal-survei-file-delete'),

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
