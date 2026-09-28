from django.contrib.auth import views as auth_views
from django.urls import path
from users.views import user_v, account_v, permission_v

urlpatterns = [
	# Utilizador (Admin / Superadmin)
	path('lista/', user_v.PesoalList, name="pesoal-list"),
	path('aumenta/', user_v.PesoalAdd, name="pesoal-add"),
	path('<int:pk>/', user_v.PesoalDetail, name="pesoal-detail"),
	path('<int:pk>/edita/', user_v.PesoalUpdate, name="pesoal-update"),
	path('<int:pk>/reset-password/', user_v.UserResetPassword, name="user-reset-password"),
	path('<int:pk>/ativu/', user_v.UserActivate, name="user-activate"),

	# Autorizasaun offline
	path('offline/', permission_v.OfflineList, name="offline-list"),
	path('offline/fo/', permission_v.OfflineGive, name="offline-give"),
	path('offline/<int:pk>/renova/', permission_v.OfflineRenew, name="offline-renew"),
	path('offline/<int:pk>/kansela/', permission_v.OfflineCancel, name="offline-cancel"),

	# Konta rasik
	path('konta/', account_v.AccountUpdate, name="user-account"),
	path('troka-password/', account_v.UserPasswordChangeView.as_view(), name="user-change-password"),
	path('troka-password/remata/', account_v.UserPasswordChangeDoneView.as_view(), name="user-change-password-done"),

	# Haluha password → email
	path('password-reset/', account_v.UserPasswordResetView.as_view(), name="password_reset"),
	path('password-reset/haruka/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name="password_reset_done"),
	path('password-reset/<uidb64>/<token>/', account_v.UserPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
	path('password-reset/remata/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name="password_reset_complete"),
]
