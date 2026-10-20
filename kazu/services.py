"""
Fluxu status kazu (fatin IDA deit). View web no API sinkron (faze 4) uza funsaun hanesan.

	Investigadór:  Rascunho / Iha Terrenu / Hein Sinál / Rejeitadu ──haruka──▶ Hein Verifikasaun
	Admin:         Hein Verifikasaun ──Verifika──▶ Verifikadu
	Superadmin:    Verifikadu ──Aprova──▶ Aprovadu          (Aprova xave to'o Admin verifika)
	Admin/Super:   Aprovadu ──Remata──▶ Remata
	Admin/Super:   Hein Verifikasaun ──Rejeita──▶ Rejeitadu   (xave hafoin verifika)
	               Rejeitadu: Verifika xave to'o Investigadór haruka fali
	Admin/Super:   Hein Verifikasaun / Rejeitadu ──Kansela──▶ Kanseladu (final: butaun hotu xave)
"""
import logging
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from config.rbac import ROLE_VERIFIKA, ROLE_APROVA, ROLE_REJEITA, ROLE_REMATA, ROLE_STATUS_KAZU, ROLE_FOLLOWUP, \
	ADMIN, SUPERADMIN, INVESTIGADOR
from kazu.models import Kazu, KazuHistoria, KazuSequence, STATUS_EDITABLE, STATUS_KAZU_CHOICES, \
	ONGOING, DRAFT, SYNCED, VERIFIED, APPROVED, COMPLETED, REJECTED, CANCELED, FOLLOWUP, STATUS_CHOICES
from notification.utils import kirim_notif, kirim_notif_role
from users.auth_utils import c_user_group, c_user_pesoal

logger = logging.getLogger('smkre.sinkron')
STATUS_LABEL = dict(STATUS_CHOICES)   # label lazy: tradus bainhira hatudu

# aksaun: (status orijen permite, status foun, role permite, razaun obrigatóriu)
ACTIONS = {
	'verifika': ([SYNCED], VERIFIED, ROLE_VERIFIKA, False),
	'aprova':   ([VERIFIED], APPROVED, ROLE_APROVA, False),
	'remata':   ([APPROVED], COMPLETED, ROLE_REMATA, False),
	'rejeita':  ([SYNCED], REJECTED, ROLE_REJEITA, True),
	'kansela':  ([SYNCED, REJECTED], CANCELED, ROLE_REJEITA, True),
}


def available_actions(user, kazu):
	# Aksaun ne'ebé utilizador ida bele halo agora (butaun ativu)
	return [b['action'] for b in action_buttons(user, kazu) if b['ativu']]


def _razaun_xave(action, status):
	# Tanba sa butaun ida xave — hatudu iha okos butaun (HP la iha tooltip)
	if status == CANCELED:
		return _('Kazu kanseladu — final.')
	if status == COMPLETED:
		return _('Kazu remata ona.')
	if status == FOLLOWUP:
		return _('Hein Investigadór halo follow-up no haruka fali.')
	if action == 'verifika':
		if status == REJECTED:
			return _('Hein Investigadór hadia no haruka fali.')
		if status in STATUS_EDITABLE:
			return _('Investigadór seidauk haruka.')
		return _('Verifika ona.')
	if action == 'aprova':
		if status == SYNCED or status in STATUS_EDITABLE:
			return _('Hein Admin verifika uluk.')
		return _('Aprova ona.')
	if action == 'remata':
		return _('Hein aprovasaun Superadmin.')
	if action == 'rejeita':
		if status == REJECTED:
			return _('Rejeita ona — hein Investigadór haruka fali.')
		if status in STATUS_EDITABLE:
			return _('Investigadór seidauk haruka.')
		return _('Xave: kazu verifika ona.')
	if action == 'kansela':
		if status in STATUS_EDITABLE:
			return _('Investigadór seidauk haruka.')
		return _('Xave: kazu verifika ona.')
	return ''


def action_buttons(user, kazu):
	# Butaun hotu ba papel utilizador nian: [{'action', 'ativu', 'presiza_nota', 'razaun'}]
	# Butaun la ativu sei hatudu (xave) ho razaun, atu utilizador hatene tanba sa.
	group = c_user_group(user)
	buttons = []
	for action, (orijen, _foun, roles, presiza_nota) in ACTIONS.items():
		if group not in roles:
			continue
		ativu = kazu.status in orijen
		buttons.append({'action': action, 'ativu': ativu, 'presiza_nota': presiza_nota,
			'razaun': '' if ativu else _razaun_xave(action, kazu.status)})
	return buttons


FOKAL_ORGANIZASAUN = 'Rede ba Rai'


def enxe_fokal(kazu, user, force=False):
	# Fokal Point RbR = Investigadór ne'ebé input kazu (ka simu follow-up). Admin bele muda iha Segimentu.
	from django.conf import settings
	from kazu.models import KazuSegimentu
	seg, _c = KazuSegimentu.objects.get_or_create(kazu=kazu)
	if seg.fokal_naran and not force:
		return seg
	pesoal = c_user_pesoal(user)
	seg.fokal_naran = ((pesoal.name if pesoal else '') or user.get_full_name() or user.username)[:150]
	seg.fokal_telemovel = ((pesoal.phone if pesoal else '') or '')[:50]
	seg.fokal_organizasaun = FOKAL_ORGANIZASAUN
	seg.fokal_enderesu = settings.PORTAL_ENDERESU[:255]
	if not seg.fokal_tipu:
		seg.fokal_tipu = 'SEKRETARIADU'
	seg.save()
	return seg


def kazu_url(kazu):
	return reverse('kazu-detail', args=[kazu.pk])


def _historia(kazu, user, antes, foun, nota='', tipu=KazuHistoria.DADUS):
	return KazuHistoria.objects.create(kazu=kazu, user=user, status_antes=antes, status_foun=foun, nota=nota, tipu=tipu)


def generate_kode(kazu):
	# RbR-LIQ-2026-0012 — kontador xave (select_for_update) atu la iha kódigu duplikadu
	tinan = kazu.data_relatoriu.year if kazu.data_relatoriu else (kazu.tinan_simu or timezone.localdate().year)
	seq, _c = KazuSequence.objects.select_for_update().get_or_create(munisipiu=kazu.munisipiu, tinan=tinan)
	seq.last += 1
	seq.save(update_fields=['last'])
	return f'RbR-{kazu.munisipiu.code}-{tinan}-{seq.last:04d}'


def refresh_auto_fields(kazu):
	# Urjente = iha nesesidade urjente; Rascunho → Iha Terrenu bainhira iha GPS + foto dahuluk
	urjente = kazu.nesesidade.exists()
	fields = []
	if kazu.urjente != urjente:
		kazu.urjente = urjente
		fields.append('urjente')
	if kazu.status == DRAFT and kazu.latitude is not None and kazu.foto_count() > 0:
		kazu.status = ONGOING
		fields.append('status')
	if fields:
		kazu.save(update_fields=fields)


def validate_submit(kazu):
	# Kondisaun minimu antes haruka ba Admin (validasaun Anexu A.9)
	erru = []
	if not kazu.konsentimentu:
		erru.append(_('Konsentimentu obrigatóriu.'))
	if kazu.latitude is None or kazu.longitude is None:
		erru.append(_('Koordenada GPS obrigatóriu.'))
	if not kazu.tipu_konflitu.exists():
		erru.append(_('Hili tipu konflitu rai.'))
	if not kazu.data_relatoriu and not kazu.tinan_simu:
		erru.append(_('Hakerek Data Simu ka Tinan Simu Kazu iha RbR.'))
	for campo, label in (('postu', _('Postu Administrativu')), ('suku', _('Suku'))):
		if not getattr(kazu, campo):
			erru.append(_('%(campo)s obrigatóriu.') % {'campo': label})
	if erru:
		raise ValidationError(erru)


@transaction.atomic
def submit_kazu(kazu, user):
	# Investigadór haruka kazu → Hein Verifikasaun + notifikasaun ba Admin no Superadmin
	kazu = Kazu.objects.select_for_update().get(pk=kazu.pk)
	if user.id not in (kazu.created_by_id, kazu.followup_ba_id):
		raise PermissionDenied
	if kazu.status not in STATUS_EDITABLE:
		raise ValidationError(_('Kazu ne\'e haruka ona.'))
	validate_submit(kazu)
	antes = kazu.status
	if not kazu.kode:
		kazu.kode = generate_kode(kazu)
	kazu.status = SYNCED
	kazu.synced_at = timezone.now()
	kazu.save(update_fields=['kode', 'status', 'synced_at'])
	nota = {REJECTED: _('Haruka fali hafoin hadia'), FOLLOWUP: _('Haruka fali hafoin follow-up')}.get(antes, '')
	_historia(kazu, user, antes, SYNCED, nota)
	pesoal = c_user_pesoal(user)
	msg = lambda: _('Kazu foun %(kode)s husi %(naran)s · %(mun)s') % {
		'kode': kazu.kode, 'naran': pesoal.name if pesoal else user.username, 'mun': kazu.munisipiu.name}
	transaction.on_commit(lambda: kirim_notif_role([ADMIN, SUPERADMIN], 'KAZU_FOUN', msg, url=kazu_url(kazu),
		actor=user, urgent=kazu.urjente, email=True))
	logger.info(f'Kazu haruka: {kazu.kode} husi {user.username}')
	return kazu


@transaction.atomic
def change_status(kazu, user, action, nota=''):
	# Verifika / Aprova / Remata / Rejeita / Kansela
	if action not in ACTIONS:
		raise ValidationError(_('Aksaun la validu.'))
	orijen, foun, roles, presiza_nota = ACTIONS[action]
	kazu = Kazu.objects.select_for_update().get(pk=kazu.pk)
	if c_user_group(user) not in roles:
		raise PermissionDenied
	if kazu.status not in orijen:
		raise ValidationError(_('Aksaun ne\'e la permite ba status %(status)s.') % {'status': STATUS_LABEL[kazu.status]})
	nota = (nota or '').strip()
	if presiza_nota and len(nota) < 5:
		raise ValidationError(_('Favor hakerek razaun (minimu karakter 5).'))
	antes = kazu.status
	kazu.status = foun
	fields = ['status']
	if foun == VERIFIED:
		kazu.verified_by, kazu.verified_at = user, timezone.now()
		fields += ['verified_by', 'verified_at']
	if foun == APPROVED:
		kazu.approved_by, kazu.approved_at = user, timezone.now()
		fields += ['approved_by', 'approved_at']
	kazu.save(update_fields=fields)
	_historia(kazu, user, antes, foun, nota)

	# Notifikasaun
	def msg():
		text = _('Kazu %(kode)s: %(status)s') % {'kode': kazu.kode, 'status': dict(STATUS_CHOICES)[foun]}
		return f'{text} — {nota}' if nota else text
	url = kazu_url(kazu)
	transaction.on_commit(lambda: kirim_notif(kazu.created_by, 'KAZU_STATUS', msg, url=url, actor=user,
		urgent=(foun == REJECTED), email=True))
	if kazu.followup_ba_id and kazu.followup_ba_id != kazu.created_by_id:      # Investigadór follow-up mós simu
		transaction.on_commit(lambda: kirim_notif(kazu.followup_ba, 'KAZU_STATUS', msg, url=url, actor=user,
			urgent=(foun == REJECTED), email=True))
	if foun == VERIFIED:
		msg_sa = lambda: _('Kazu %(kode)s verifika ona husi Admin. Hein ita-nia aprovasaun.') % {'kode': kazu.kode}
		transaction.on_commit(lambda: kirim_notif_role([SUPERADMIN], 'KAZU_STATUS', msg_sa, url=url, actor=user,
			urgent=kazu.urjente, email=True))
	logger.info(f'Kazu {kazu.kode}: {antes} → {foun} husi {user.username}')
	return kazu


@transaction.atomic
def change_status_kazu(kazu, user, status_kazu, nota=''):
	# Status prosesu kazu (Abertu → Investigasaun → Aksaun Legál → Taka)
	if c_user_group(user) not in ROLE_STATUS_KAZU:
		raise PermissionDenied
	if status_kazu not in dict(STATUS_KAZU_CHOICES):
		raise ValidationError(_('Status kazu la validu.'))
	if kazu.status not in (VERIFIED, APPROVED, COMPLETED, FOLLOWUP):
		raise ValidationError(_('Kazu tenke verifika uluk.'))
	antes = kazu.status_kazu
	if antes == status_kazu:
		return kazu
	kazu.status_kazu = status_kazu
	kazu.save(update_fields=['status_kazu'])
	_historia(kazu, user, antes, status_kazu, nota, tipu=KazuHistoria.KAZU)
	if status_kazu == 'AKSAUN_LEGAL':
		from legal.services import notifika_aksaun_legal      # import iha laran: evita import sirkulár
		notifika_aksaun_legal(kazu, user)
	return kazu


# ══════════════ FOLLOW-UP (tuun fali ba terrenu) ══════════════
STATUS_FOLLOWUP_ORIJEN = (VERIFIED, APPROVED)


def investigador_followup(kazu):
	# Investigadór ativu iha munisípiu kazu nian (bele simu follow-up)
	from django.contrib.auth.models import User
	return User.objects.filter(groups__name=INVESTIGADOR, is_active=True,
		pesoaluser__pesoal__munisipiu=kazu.munisipiu).select_related('pesoaluser__pesoal').order_by('pesoaluser__pesoal__name')


def can_followup(user, kazu):
	return c_user_group(user) in ROLE_FOLLOWUP and kazu.status in STATUS_FOLLOWUP_ORIJEN


@transaction.atomic
def followup_kazu(kazu, user, investigador, nota):
	# Loke fali kazu → Investigadór tuun ba terrenu (survei foun), edita online ka offline, haruka fali → Verifika → Aprova
	kazu = Kazu.objects.select_for_update().get(pk=kazu.pk)
	if c_user_group(user) not in ROLE_FOLLOWUP:
		raise PermissionDenied
	if kazu.status not in STATUS_FOLLOWUP_ORIJEN:
		raise ValidationError(_('Follow-up bele halo de\'it ba kazu Verifikadu ka Aprovadu.'))
	nota = (nota or '').strip()
	if len(nota) < 5:
		raise ValidationError(_('Favor hakerek instrusaun follow-up (minimu karakter 5).'))
	if investigador is None or not investigador_followup(kazu).filter(pk=investigador.pk).exists():
		raise ValidationError(_('Hili Investigadór ativu husi munisípiu kazu nian.'))
	antes = kazu.status
	kazu.status, kazu.followup_ba, kazu.followup_at = FOLLOWUP, investigador, timezone.now()
	kazu.save(update_fields=['status', 'followup_ba', 'followup_at'])
	pesoal = c_user_pesoal(investigador)
	naran = pesoal.name if pesoal else investigador.username
	_historia(kazu, user, antes, FOLLOWUP, _('Follow-up ba %(naran)s: %(nota)s') % {'naran': naran, 'nota': nota})
	enxe_fokal(kazu, investigador, force=True)            # Fokal point = Investigadór follow-up
	url = kazu_url(kazu)
	msg = lambda: _('Follow-up: kazu %(kode)s — tuun fali ba terrenu. %(nota)s') % {'kode': kazu.kode, 'nota': nota}
	transaction.on_commit(lambda: kirim_notif(investigador, 'KAZU_STATUS', msg, url=url, actor=user, urgent=True, email=True))
	logger.info(f'Follow-up kazu {kazu.kode} ba {investigador.username} husi {user.username}')
	return kazu
