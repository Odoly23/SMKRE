from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from publiku.services import estatistika


class APIPortalEstatistika(APIView):
	# Públiku (la presiza login): dadus agregadu no anónimu deit. Limite pedidu kada IP.
	authentication_classes = []
	permission_classes = [AllowAny]
	throttle_classes = [AnonRateThrottle]

	def get(self, request, format=None):
		response = Response(estatistika(request.GET))
		response['Cache-Control'] = 'public, max-age=300'
		return response
