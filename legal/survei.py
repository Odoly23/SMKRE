"""Survei legál (Perguntas Xave Sira Legal): permisaun, kódigu, haruka, verifika."""
import logging
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from config.rbac import ROLE_SURVEI_INPUT, ROLE_SURVEI_HAREE, ROLE_SURVEI_VERIFIKA, ADMIN, SUPERADMIN, OFISIAL_LEGAL
from legal.models import SurveiLegal, SurveiSequence
from notification.utils import kirim_notif, kirim_notif_role
from users.auth_utils import c_user_group, c_user_offline, c_user_pesoal

logger = logging.getLogger('smkre.sinkron')


def input_ativu(user):
	# Butaun "Input Legál" mosu de'it bainhira Admin fó autorizasaun input (data hahú–remata) ne'ebé validu
	return c_user_group(user) in ROLE_SURVEI_INPUT and bool(c_user_offline(user))


def survei_queryset(user):
	qs = SurveiLegal.objects.select_related('munisipiu', 'suku', 'kazu', 'created_by__pesoaluser__pesoal')
	group = c_user_group(user)
	if group == OFISIAL_LEGAL:
		return qs                                   # Ofisiál Legál haree survei hotu (servisu hamutuk)
	if group in ROLE_SURVEI_HAREE:
		return qs.exclude(status=SurveiLegal.RASCUNHO)
	return qs.none()


def can_edit_survei(user, s):
	return s.created_by_id == user.id and s.editable and input_ativu(user)


def _kode(s):
	tinan = s.data_survei.year
	seq, _c = SurveiSequence.objects.select_for_update().get_or_create(munisipiu=s.munisipiu, tinan=tinan)
	seq.last += 1
	seq.save(update_fields=['last'])
	return f'LGL-{s.munisipiu.code}-{tinan}-{seq.last:04d}'


def valida_haruka(s):
	erru = []
	if not s.munisipiu_id:
		erru.append(_('Munisípiu obrigatóriu.'))
	if not s.parte_naran:
		erru.append(_('Naran parte (disputante) obrigatóriu.'))
	if not s.meius:
		erru.append(_('Hili meius ka maneira hetan rai.'))
	if erru:
		raise ValidationError(erru)


@transaction.atomic
def haruka(s, user):
	s = SurveiLegal.objects.select_for_update().get(pk=s.pk)
	if s.created_by_id != user.id:
		raise PermissionDenied
	if not s.editable:
		raise ValidationError(_("Survei ne'e haruka ona."))
	valida_haruka(s)
	if not s.kode:
		s.kode = _kode(s)
	s.status, s.haruka_at, s.nota_rejeita = SurveiLegal.HARUKA, timezone.now(), ''
	s.save(update_fields=['kode', 'status', 'haruka_at', 'nota_rejeita'])
	pesoal = c_user_pesoal(user)
	url = reverse('legal-survei-detail', args=[s.pk])
	msg = lambda: _('Survei legál foun %(kode)s husi %(naran)s · %(mun)s') % {
		'kode': s.kode, 'naran': pesoal.name if pesoal else user.username, 'mun': s.munisipiu.name}
	transaction.on_commit(lambda: kirim_notif_role([ADMIN, SUPERADMIN], 'KAZU_FOUN', msg, url=url, actor=user, email=True))
	logger.info(f'Survei legál haruka: {s.kode} husi {user.username}')
	return s


@transaction.atomic
def verifika(s, user, aprova=True, nota=''):
	s = SurveiLegal.objects.select_for_update().get(pk=s.pk)
	if c_user_group(user) not in ROLE_SURVEI_VERIFIKA:
		raise PermissionDenied
	if s.status != SurveiLegal.HARUKA:
		raise ValidationError(_('Survei ne\'e la hein verifikasaun.'))
	nota = (nota or '').strip()
	if not aprova and len(nota) < 5:
		raise ValidationError(_('Favor hakerek razaun (minimu karakter 5).'))
	if aprova:
		s.status, s.verified_by, s.verified_at = SurveiLegal.VERIFIKADU, user, timezone.now()
	else:
		s.status, s.nota_rejeita = SurveiLegal.REJEITADU, nota[:255]
	s.save(update_fields=['status', 'verified_by', 'verified_at', 'nota_rejeita'])
	url = reverse('legal-survei-detail', args=[s.pk])
	msg = lambda: (_('Survei %(kode)s verifika ona.') if aprova else _('Survei %(kode)s rejeita: %(nota)s')) % {'kode': s.kode, 'nota': nota}
	transaction.on_commit(lambda: kirim_notif(s.created_by, 'KAZU_STATUS', msg, url=url, actor=user, urgent=not aprova, email=True))
	return s


# ── Sinkron husi app offline (HP) ──
SURVEI_CAMPO_LISTA = ('dok_identifikasaun', 'dok_relevante', 'fotografia')
MAX_FILE_HP = 10


@transaction.atomic
def sync_survei(user, data):
	"""Survei JSON husi HP → SurveiLegal (idempotente tuir id UUID). Retorna (survei, foun)."""
	from django.utils.dateparse import parse_datetime
	from legal.forms import SurveiLegalForm, SURVEI_KAMPU
	from sinkron.services import parse_uuid, check_permission_window, _gps
	pk = parse_uuid(data.get('id'))
	kria_iha = parse_datetime(str(data.get('kria_iha') or ''))
	if not kria_iha:
		raise ValidationError(_('Data kria la validu.'))
	if timezone.is_naive(kria_iha):
		kria_iha = timezone.make_aware(kria_iha)
	s = SurveiLegal.objects.select_for_update().filter(pk=pk).first()
	if s and s.created_by_id != user.id:
		raise PermissionDenied
	if s and not s.editable:
		return s, False                                 # haruka ona (koko fali)
	if not s:
		if c_user_group(user) not in ROLE_SURVEI_INPUT:
			raise PermissionDenied
		check_permission_window(user, kria_iha)
	form_data = {}
	for c in SURVEI_KAMPU:
		v = data.get(c)
		if v is None:
			continue
		form_data[c] = [str(x) for x in v] if c in SURVEI_CAMPO_LISTA and isinstance(v, list) else v
	form_data['latitude'], form_data['longitude'] = _gps(data.get('latitude')), _gps(data.get('longitude'))
	from django.http import QueryDict
	qd = QueryDict(mutable=True)
	for k, v in form_data.items():
		if isinstance(v, list):
			qd.setlist(k, v)
		elif v not in ('', None):
			qd[k] = str(v)
	form = SurveiLegalForm(qd, instance=s)
	if not form.is_valid():
		raise ValidationError({k: [str(m) for m in v] for k, v in form.errors.items()})
	obj = form.save(commit=False)
	foun = s is None
	if foun:
		obj.pk, obj.created_by = pk, user
	obj.save()
	if foun:
		SurveiLegal.objects.filter(pk=obj.pk).update(created_at=min(kria_iha, timezone.now()))
	logger.info(f'Survei legál sinkron: {obj.pk} husi {user.username} ({"foun" if foun else "atualiza"})')
	return obj, foun


@transaction.atomic
def sync_survei_file(user, s, file_id, tipu, f, naran=''):
	from legal.models import SurveiLegalFile
	from legal.services import valida_file
	from sinkron.services import parse_uuid
	fid = parse_uuid(file_id)
	uluk = SurveiLegalFile.objects.filter(pk=fid).first()
	if uluk:
		if uluk.survei_id != s.pk:
			raise PermissionDenied
		return uluk, False
	if s.created_by_id != user.id or not s.editable:
		raise PermissionDenied
	if s.files.count() >= MAX_FILE_HP * 2:
		raise ValidationError(_('File barak liu.'))
	if tipu not in (SurveiLegalFile.FOTO, SurveiLegalFile.DOKUMENTU):
		raise ValidationError(_('Tipu file la validu.'))
	valida_file(f)
	obj = SurveiLegalFile.objects.create(pk=fid, survei=s, tipu=tipu, file=f, naran=(naran or '')[:150], uploaded_by=user)
	return obj, True
