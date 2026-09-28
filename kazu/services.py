"""
Fluxu status kazu (fatin IDA deit). View web no API sinkron (faze 4) uza funsaun hanesan.

	Investigadór:  Rascunho / Iha Terrenu / Hein Sinál / Rejeitadu ──haruka──▶ Hein Verifikasaun
	Admin:         Hein Verifikasaun ──Verifika──▶ Verifikadu
	Superadmin:    Verifikadu ──Aprova──▶ Aprovadu
	Admin/Super:   Aprovadu ──Remata──▶ Remata
	Admin/Super:   Hein Verifikasaun / Verifikadu ──Rejeita──▶ Rejeitadu (Investigadór hadia)
	Admin/Super:   Hein Verifikasaun / Verifikadu / Rejeitadu ──Kansela──▶ Kanseladu (final)
"""
import logging
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from config.rbac import ROLE_VERIFIKA, ROLE_APROVA, ROLE_REJEITA, ROLE_REMATA, ROLE_STATUS_KAZU, \
	ADMIN, SUPERADMIN
from kazu.models import Kazu, KazuHistoria, KazuSequence, STATUS_EDITABLE, STATUS_KAZU_CHOICES, \
	ONGOING, DRAFT, SYNCED, VERIFIED, APPROVED, COMPLETED, REJECTED, CANCELED, STATUS_CHOICES
from notification.utils import kirim_notif, kirim_notif_role
from users.auth_utils import c_user_group, c_user_pesoal

logger = logging.getLogger('smkre.sinkron')
STATUS_LABEL = dict(STATUS_CHOICES)   # label lazy: tradus bainhira hatudu

# aksaun: (status orijen permite, status foun, role permite, razaun obrigatóriu)
ACTIONS = {
	'verifika': ([SYNCED], VERIFIED, ROLE_VERIFIKA, False),
	'aprova':   ([VERIFIED], APPROVED, ROLE_APROVA, False),
	'remata':   ([APPROVED], COMPLETED, ROLE_REMATA, False),
	'rejeita':  ([SYNCED, VERIFIED], REJECTED, ROLE_REJEITA, True),
	'kansela':  ([SYNCED, VERIFIED, REJECTED], CANCELED, ROLE_REJEITA, True),
}


def available_actions(user, kazu):
	# Butaun aksaun ne'ebé utilizador ida bele haree iha detalla kazu
	group = c_user_group(user)
	return [name for name, (orijen, _n, roles, _r) in ACTIONS.items() if kazu.status in orijen and group in roles]


def kazu_url(kazu):
	return reverse('kazu-detail', args=[kazu.pk])


def _historia(kazu, user, antes, foun, nota='', tipu=KazuHistoria.DADUS):
	return KazuHistoria.objects.create(kazu=kazu, user=user, status_antes=antes, status_foun=foun, nota=nota, tipu=tipu)


def generate_kode(kazu):
	# SMKRE-LIQ-2026-00012 — kontador xave (select_for_update) atu la iha kódigu duplikadu
	tinan = (kazu.data_relatoriu or timezone.localdate()).year
	seq, _c = KazuSequence.objects.select_for_update().get_or_create(munisipiu=kazu.munisipiu, tinan=tinan)
	seq.last += 1
	seq.save(update_fields=['last'])
	return f'SMKRE-{kazu.munisipiu.code}-{tinan}-{seq.last:05d}'


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
	for campo, label in (('data_relatoriu', _('Data Relatóriu')), ('data_akontesimentu', _('Data Akontesimentu')),
			('postu', _('Postu Administrativu')), ('suku', _('Suku')), ('deskrisaun', _('Deskrisaun Insidente'))):
		if not getattr(kazu, campo):
			erru.append(_('%(campo)s obrigatóriu.') % {'campo': label})
	if erru:
		raise ValidationError(erru)


@transaction.atomic
def submit_kazu(kazu, user):
	# Investigadór haruka kazu → Hein Verifikasaun + notifikasaun ba Admin no Superadmin
	kazu = Kazu.objects.select_for_update().get(pk=kazu.pk)
	if kazu.created_by_id != user.id:
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
	nota = _('Haruka fali hafoin hadia') if antes == REJECTED else ''
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
	if kazu.status not in (VERIFIED, APPROVED, COMPLETED):
		raise ValidationError(_('Kazu tenke verifika uluk.'))
	antes = kazu.status_kazu
	if antes == status_kazu:
		return kazu
	kazu.status_kazu = status_kazu
	kazu.save(update_fields=['status_kazu'])
	_historia(kazu, user, antes, status_kazu, nota, tipu=KazuHistoria.KAZU)
	return kazu
