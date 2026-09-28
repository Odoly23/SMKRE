"""
Regra sinkron offline (fatin IDA deit). API iha sinkron/api/views.py uza funsaun sira ne'e.

	HP (offline) ──kazu JSON──▶ sync_kazu()        → Hein Sinál (PENDING) iha server
	HP           ──foto/vídeo──▶ sync_evidensia()  → evidénsia ida-ida (bele koko fali)
	HP           ──haruka──────▶ kazu.services.submit_kazu() → Hein Verifikasaun + notifikasaun Admin

Regra autorizasaun: kazu tenke KRIA iha HP durante períodu autorizasaun offline ne'ebé Admin fó.
Autorizasaun remata ona → Investigadór labele kria kazu foun, maibé bele nafatin sinkron kazu uluk.
Kada pasu idempotente (ID UUID husi HP): koneksaun kotu → koko fali la kria duplikadu.
"""
import logging
import uuid
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _
from config.upload_utils import compress_image
from kazu.forms import KazuForm, AfetaduForm, InsidenteForm, AtorForm, EvidensiaForm
from kazu.models import Kazu, Evidensia, KazuHistoria, STATUS_EDITABLE, PENDING
from kazu.services import refresh_auto_fields
from users.auth_utils import c_user_pesoal
from users.models import OfflinePermission

logger = logging.getLogger('smkre.sinkron')

TOLERANSIA_RELOJIU = timedelta(minutes=10)        # relójiu HP bele sala uitoan
KAZU_CAMPO = ['titulu', 'data_relatoriu', 'postu', 'suku', 'aldeia', 'latitude', 'longitude', 'gps_akurasia',
	'data_akontesimentu', 'tipu_konflitu', 'tipu_seluk', 'tipu_rai', 'deskrisaun',
	'estragu', 'estragu_seluk', 'nesesidade', 'konsentimentu', 'observasaun']
# lista laran kazu: (xave JSON, formuláriu, máximu)
KAZU_LISTA = [('afetadu', AfetaduForm, 5), ('insidente', InsidenteForm, 10), ('ator', AtorForm, 20)]


class SyncError(ValidationError):
	# Erru validasaun ho kampu (HP hatudu iha pasu formuláriu ne'ebé loos)
	pass


def parse_uuid(value):
	try:
		return uuid.UUID(str(value))
	except (ValueError, TypeError, AttributeError):
		raise ValidationError(_('ID la validu.'))


def check_permission_window(user, kria_iha):
	# Kazu tenke kria iha HP durante autorizasaun offline (inklui ida ne'ebé remata ka kansela depois)
	if kria_iha > timezone.now() + TOLERANSIA_RELOJIU:
		raise ValidationError(_('Data kria kazu iha futuru. Favor haree data no oras iha HP.'))
	ok = OfflinePermission.objects.filter(user=user, start_date__lte=kria_iha + TOLERANSIA_RELOJIU, end_date__gte=kria_iha) \
		.filter(Q(is_active=True) | Q(cancelled_at__gt=kria_iha)).exists()
	if not ok:
		raise ValidationError(_("Kazu ne'e kria iha li'ur períodu autorizasaun offline. Kontaktu Admin."))


def _gps(value):
	# GPS husi HP bele iha desimál barak → arredonda ba 6 (±0.1 m)
	if value in (None, ''):
		return ''
	try:
		return str(Decimal(str(value)).quantize(Decimal('0.000001')))
	except (InvalidOperation, ValueError):
		return value


def _form_data(data):
	form_data = {campo: data.get(campo) for campo in KAZU_CAMPO if data.get(campo) is not None}
	form_data['latitude'] = _gps(data.get('latitude'))
	form_data['longitude'] = _gps(data.get('longitude'))
	return form_data


@transaction.atomic
def sync_kazu(user, data):
	# Simu kazu husi HP. Retorna (kazu, foun_ka_lae). Kazu haruka ona → retorna de'it (la muda).
	pesoal = c_user_pesoal(user)
	if not pesoal or not pesoal.munisipiu:
		raise ValidationError(_('Ita seidauk iha munisípiu knaar. Kontaktu Admin.'))
	kazu_id = parse_uuid(data.get('id'))
	kria_iha = parse_datetime(str(data.get('kria_iha') or ''))
	if not kria_iha:
		raise ValidationError(_('Data kria kazu la iha.'))
	if timezone.is_naive(kria_iha):
		kria_iha = timezone.make_aware(kria_iha)
	check_permission_window(user, kria_iha)

	instance = Kazu.objects.select_for_update().filter(pk=kazu_id).first()
	if instance:
		if instance.created_by_id != user.id:
			raise PermissionDenied
		if instance.status not in STATUS_EDITABLE:
			return instance, False                 # sinkron ona (koko fali) → la muda buat ida

	# Validasaun hanesan formuláriu web (GPS iha TL, akurasia ≤ 50 m, lokalizasaun, konsentimentu...)
	form = KazuForm(data=_form_data(data), instance=instance, munisipiu_knaar=pesoal.munisipiu, submit=True)
	erru = {} if form.is_valid() else {k: list(v) for k, v in form.errors.items()}
	lista = []
	for xave, Form, maximu in KAZU_LISTA:
		items = data.get(xave) or []
		if not isinstance(items, list) or len(items) > maximu:
			erru[xave] = [_('Máximu %(n)s.') % {'n': maximu}]
			continue
		for n, row in enumerate(items):
			f = Form(data=row if isinstance(row, dict) else {})
			if f.is_valid():
				lista.append(f)
			else:
				erru.update({f'{xave}.{n}.{k}': list(v) for k, v in f.errors.items()})
	if erru:
		raise SyncError(erru)

	foun = instance is None
	obj = form.save(commit=False)
	if foun:
		obj.id = kazu_id
		obj.created_by = user
		obj.status = PENDING
	obj.save()
	form.save_m2m()
	# Lista laran: troka hotu (HP haruka lista kompletu)
	obj.afetadu.all().delete()
	obj.insidente.all().delete()
	obj.ator.all().delete()
	for f in lista:
		child = f.save(commit=False)
		child.kazu = obj
		child.save()
	refresh_auto_fields(obj)
	KazuHistoria.objects.create(kazu=obj, user=user, tipu=KazuHistoria.EDITA, status_foun=obj.status, nota='SINKRON')
	logger.info(f'Sinkron kazu {obj.pk} ({"foun" if foun else "atualiza"}) husi {user.username}')
	return obj, foun


@transaction.atomic
def sync_evidensia(user, kazu, ev_id, tipu, f):
	# Foto (kompresa, EXIF hamoos) ka vídeo husi kámera HP. Retorna (evidensia, foun_ka_lae).
	kazu = Kazu.objects.select_for_update().get(pk=kazu.pk)
	if kazu.created_by_id != user.id:
		raise PermissionDenied
	ev_id = parse_uuid(ev_id)
	ev = Evidensia.objects.filter(pk=ev_id).first()
	if ev:
		if ev.kazu_id != kazu.pk:
			raise PermissionDenied
		return ev, False                           # upload ona (koko fali)
	if kazu.status not in STATUS_EDITABLE:
		raise ValidationError(_("Kazu ne'e haruka ona."))
	if tipu not in (Evidensia.FOTO, Evidensia.VIDEO):
		raise ValidationError(_('HP bele haruka foto ka vídeu deit.'))
	form = EvidensiaForm(data={'tipu': tipu}, files={'file': f}, kazu=kazu)
	if not form.is_valid():
		raise SyncError({k: list(v) for k, v in form.errors.items()})
	ev = form.save(commit=False)
	ev.id = ev_id
	ev.kazu = kazu
	ev.uploaded_by = user
	if tipu == Evidensia.FOTO:
		small = compress_image(f)
		if small:
			ev.file = small
	ev.latitude, ev.longitude = kazu.latitude, kazu.longitude
	ev.save()
	refresh_auto_fields(kazu)
	logger.info(f'Sinkron evidénsia {tipu} ba kazu {kazu.pk} husi {user.username}')
	return ev, True
