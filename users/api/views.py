import logging
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from config.rbac import INVESTIGADOR
from users.auth_utils import c_user_group, c_user_pesoal, c_user_offline
from users.models import OfflinePermission

logger = logging.getLogger('smkre.sinkron')


def _check_offline(user):
	# Token sinkron ba Investigadór ne'ebé simu ona autorizasaun offline husi Admin.
	# Autorizasaun remata → token nafatin (bele sinkron), maibé app labele kria kazu foun (offline_ativu = False).
	if c_user_group(user) != INVESTIGADOR:
		raise serializers.ValidationError(_('Token sinkron ba Investigadór deit.'))
	if not OfflinePermission.objects.filter(user=user).exists():
		raise serializers.ValidationError(_('Autorizasaun offline la ativu. Kontaktu Admin.'))


def _offline_info(user):
	perm = c_user_offline(user)
	return {'offline_ativu': bool(perm), 'offline_until': perm.end_date.isoformat() if perm else None}


class OfflineTokenObtainSerializer(TokenObtainPairSerializer):
	username_field = 'username'

	def validate(self, attrs):
		attrs['username'] = (attrs.get('username') or '').strip().lower()
		data = super().validate(attrs)
		_check_offline(self.user)
		data.update(_offline_info(self.user))
		logger.info(f'Token sinkron: {self.user.username}')
		return data


class OfflineTokenRefreshSerializer(TokenRefreshSerializer):
	def validate(self, attrs):
		from django.contrib.auth.models import User
		refresh = RefreshToken(attrs['refresh'])
		user = User.objects.filter(pk=refresh.payload.get('user_id'), is_active=True).first()
		if not user:
			raise serializers.ValidationError(_('Utilizador la ativu.'))
		_check_offline(user)
		data = super().validate(attrs)
		data.update(_offline_info(user))
		return data


class APIOfflineTokenObtain(TokenObtainPairView):
	serializer_class = OfflineTokenObtainSerializer


class APIOfflineTokenRefresh(TokenRefreshView):
	serializer_class = OfflineTokenRefreshSerializer


class APIMe(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, format=None):
		pesoal = c_user_pesoal(request.user)
		return Response({
			'email': request.user.email,
			'naran': pesoal.name if pesoal else '',
			'role': c_user_group(request.user),
			'munisipiu': pesoal.munisipiu_id if pesoal else None,
			'munisipiu_naran': pesoal.munisipiu.name if pesoal and pesoal.munisipiu else '',
			**_offline_info(request.user),
		})
