from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from config.permissions import HasRole
from config.rbac import INVESTIGADOR
from custom.models import PostuAdministrativu, Suku, Aldeia, TipuKonflitu, TipuRai, TipuEviksaun, \
	TipuAtor, EstraguPatrimoniu, NesesidadeUrjente
from kazu.models import Kazu, KazuHistoria, STATUS_CHOICES, STATUS_EDITABLE, REJECTED
from kazu.services import submit_kazu
from sinkron.services import sync_kazu, sync_evidensia
from users.auth_utils import c_user_pesoal


def _erru(e):
	# ValidationError → {'erru': {kampu: [mensajen]}} ba HP
	if hasattr(e, 'message_dict'):
		return {'erru': e.message_dict}
	return {'erru': {'__all__': e.messages}}


class _SinkronAPI(APIView):
	# Token JWT (app offline) + Investigadór deit. Mensajen iha Tetun (app offline iha Tetun).
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticated, HasRole(INVESTIGADOR)]

	def dispatch(self, request, *args, **kwargs):
		with translation.override('tet'):
			return super().dispatch(request, *args, **kwargs)


def _lista(qs, *extra):
	return [dict({'id': o.pk, 'name': o.name}, **{k: getattr(o, k) for k in extra}) for o in qs]


class APIOpsaun(_SinkronAPI):
	# Dadus master ba formuláriu offline: munisípiu knaar + postu/suku/aldeia + opsaun padronizadu
	def get(self, request, format=None):
		pesoal = c_user_pesoal(request.user)
		mun = pesoal.munisipiu if pesoal else None
		if not mun:
			return Response({'erru': {'__all__': [_('Ita seidauk iha munisípiu knaar. Kontaktu Admin.')]}}, status=400)
		postu = PostuAdministrativu.active.filter(munisipiu=mun)
		suku = Suku.active.filter(postu__in=postu)
		aldeia = Aldeia.active.filter(suku__in=suku)
		data = {
			'munisipiu': {'id': mun.pk, 'code': mun.code, 'name': mun.name},
			'postu': _lista(postu),
			'suku': _lista(suku, 'postu_id'),
			'aldeia': _lista(aldeia, 'suku_id'),
			'tipu_konflitu': _lista(TipuKonflitu.active.all(), 'presiza_esplika'),
			'tipu_rai': _lista(TipuRai.active.all()),
			'tipu_eviksaun': _lista(TipuEviksaun.active.all()),
			'tipu_ator': _lista(TipuAtor.active.all()),
			'estragu': _lista(EstraguPatrimoniu.active.all()),
			'nesesidade': _lista(NesesidadeUrjente.active.all()),
		}
		return Response(data)


class APIKazuLista(_SinkronAPI):
	# GET: status kazu rasik (HP hatudu Verifikadu / Rejeitadu...) · POST: simu kazu husi HP
	parser_classes = [JSONParser]

	def get(self, request, format=None):
		status_label = dict(STATUS_CHOICES)
		objects = Kazu.objects.filter(created_by=request.user).order_by('-updated_at')[:100]
		rejeita = {h.kazu_id: h.nota for h in KazuHistoria.objects.filter(kazu__in=objects, status_foun=REJECTED).order_by('created_at')}
		data = [{
			'id': str(k.pk), 'kode': k.kode, 'status': k.status, 'status_label': str(status_label[k.status]),
			'nota': rejeita.get(k.pk, '') if k.status == REJECTED else '', 'updated_at': k.updated_at.isoformat(),
		} for k in objects]
		return Response({'kazu': data})

	def post(self, request, format=None):
		if not isinstance(request.data, dict):
			return Response({'erru': {'__all__': [_('Dadus la validu.')]}}, status=400)
		try:
			try:
				kazu, foun = sync_kazu(request.user, request.data)
			except IntegrityError:
				# Pedidu rua paralelu ho ID hanesan → koko fali dala ida (dalan idempotente)
				kazu, foun = sync_kazu(request.user, request.data)
		except PermissionDenied:
			return Response({'erru': {'__all__': [_('La iha asesu.')]}}, status=403)
		except ValidationError as e:
			return Response(_erru(e), status=400)
		return Response({'id': str(kazu.pk), 'kode': kazu.kode, 'status': kazu.status,
			'foto': kazu.foto_count(), 'video': kazu.video_count()}, status=201 if foun else 200)


class APIEvidensia(_SinkronAPI):
	# Foto / vídeo ida-ida (multipart): id (UUID husi HP), tipu, file
	parser_classes = [MultiPartParser]

	def post(self, request, uuid, format=None):
		kazu = get_object_or_404(Kazu, pk=uuid, created_by=request.user)
		f = request.FILES.get('file')
		if not f:
			return Response({'erru': {'file': [_('File la iha.')]}}, status=400)
		try:
			try:
				ev, foun = sync_evidensia(request.user, kazu, request.data.get('id'), request.data.get('tipu'), f)
			except IntegrityError:
				f.seek(0)
				ev, foun = sync_evidensia(request.user, kazu, request.data.get('id'), request.data.get('tipu'), f)
		except PermissionDenied:
			return Response({'erru': {'__all__': [_('La iha asesu.')]}}, status=403)
		except ValidationError as e:
			return Response(_erru(e), status=400)
		return Response({'id': str(ev.pk), 'tipu': ev.tipu}, status=201 if foun else 200)


class APIHaruka(_SinkronAPI):
	# Pasu ikus: kazu kompletu → Hein Verifikasaun (kódigu SMKRE-...) + notifikasaun Admin/Superadmin
	def post(self, request, uuid, format=None):
		kazu = get_object_or_404(Kazu, pk=uuid, created_by=request.user)
		if kazu.status not in STATUS_EDITABLE:          # haruka ona (koko fali)
			return Response({'id': str(kazu.pk), 'kode': kazu.kode, 'status': kazu.status})
		try:
			kazu = submit_kazu(kazu, request.user)
		except ValidationError as e:
			return Response(_erru(e), status=400)
		return Response({'id': str(kazu.pk), 'kode': kazu.kode, 'status': kazu.status}, status=status.HTTP_200_OK)
