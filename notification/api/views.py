from django.utils import timezone
from django.utils.timesince import timesince
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from notification.models import Notification

NOTIF_MAX = 5


# Notif: total seidauk lee (ba badge 🔔)
class APINotifTotal(APIView):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	def get(self, request, format=None):
		objects = Notification.objects.filter(recipient=request.user, is_read=False).count()
		return Response({'value': objects})


# Notif: lista 5 ikus (ba dropdown 🔔) — máximu NOTIF_MAX
class APINotifLatest(APIView):
	authentication_classes = [SessionAuthentication, JWTAuthentication]
	permission_classes = [IsAuthenticated]
	def get(self, request, format=None):
		objects = Notification.objects.filter(recipient=request.user, is_read=False)[:NOTIF_MAX]   # urjente uluk, depois foun
		data = [{
			'id': o.pk, 'message': o.message, 'urgent': o.is_urgent, 'tipu': o.tipu,
			'ago': timesince(o.created_at, timezone.now()).split(',')[0],
		} for o in objects]
		return Response({'value': len(data), 'objects': data})
