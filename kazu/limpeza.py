"""Limpeza automátiku kazu ne'ebé la prosesa (regra Rede ba Rai).

	Pasu 1 — kansela (bele restaura):
		Hein Verifikasaun (SYNCED) loron 30 la verifika      → Kanseladu automátiku
		Verifikadu (VERIFIED)      loron 30 la aprova         → Kanseladu automátiku
	Pasu 2 — hamoos permanente:
		Kanseladu automátiku loron 30 (Admin la restaura)     → hamoos husi base de dadus + file evidénsia

	Exetu (la toka): kazu import (Excel / Airtable, dadus istóriku) no kazu ho dadus legál
	(survei / nota / dokumentu legál). Kanselamentu manuál husi Admin la hamoos.
	Lembrete: Admin (verifika) / Superadmin (aprova) iha loron 21 no 28; antes hamoos iha loron 23.
	Konta hahú husi settings.LIMPEZA_HAHU (kazu tuan hetan loron 30 hafoin ativa).
	Hala'o kada loron: kazu.tasks.limpeza_automatiku (Celery Beat) ka `python manage.py knaar_loron`.
"""
import logging
from datetime import datetime, time, timedelta
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from config.rbac import ADMIN, SUPERADMIN, ROLE_REJEITA
from kazu.models import Kazu, KazuHistoria, SYNCED, VERIFIED, CANCELED
from notification.utils import kirim_notif, kirim_notif_role
from users.auth_utils import c_user_group

logger = logging.getLogger('smkre.seguransa')

LORON = 30                      # kansela hafoin loron 30; hamoos loron 30 hafoin kansela
LEMBRA = (21, 28)               # lembrete antes kansela
LEMBRA_HAMOOS = 23              # lembrete antes hamoos (loron 7 tan)
# status → (kampu data hahú konta, papél ne'ebé tenke hala'o)
REGRA = {
	SYNCED: ('synced_at', [ADMIN]),
	VERIFIED: ('verified_at', [SUPERADMIN]),
}


# razaun iha lian utilizador: "la verifika" / "la aprova"
def _razaun(status):
	return _('la verifika') if status == SYNCED else _('la aprova')


# data hahú regra (settings.LIMPEZA_HAHU) nu'udar datetime ho fuso orário
def _hahu():
	d = datetime.strptime(str(settings.LIMPEZA_HAHU), '%Y-%m-%d').date()
	return timezone.make_aware(datetime.combine(d, time()))


# kazu ne'ebé bele tama iha regra: la'ós import no la iha dadus legál
def _baze():
	from legal.models import DokumentuLegal, NotaLegal, SurveiLegal
	legal = set(NotaLegal.objects.values_list('kazu_id', flat=True)) | \
		set(DokumentuLegal.objects.exclude(kazu=None).values_list('kazu_id', flat=True)) | \
		set(SurveiLegal.objects.exclude(kazu=None).values_list('kazu_id', flat=True))
	return Kazu.objects.filter(importasaun__isnull=True).exclude(pk__in=legal)


# loron hira ona kazu hein (konta husi data status ka husi LIMPEZA_HAHU, ida ne'ebé foun liu)
def loron_hein(kazu, agora=None):
	campo = REGRA[kazu.status][0] if kazu.status in REGRA else None
	inisiu = getattr(kazu, campo, None) if campo else kazu.kansela_auto_iha
	inisiu = max(filter(None, [inisiu or kazu.created_at, _hahu()]))
	return ((agora or timezone.now()) - inisiu).days


# kansela kazu ida automátiku (rai status uluk atu Admin bele restaura)
@transaction.atomic
def _kansela(kazu, agora):
	antes = kazu.status
	nota = _('Kansela automátiku: loron %(n)s %(r)s. Sei hamoos permanente hafoin loron %(n)s se la restaura.') % {'n': LORON, 'r': _razaun(antes)}
	kazu.kansela_auto_antes, kazu.kansela_auto_iha, kazu.status = antes, agora, CANCELED
	kazu.save(update_fields=['status', 'kansela_auto_iha', 'kansela_auto_antes'])
	KazuHistoria.objects.create(kazu=kazu, user=None, status_antes=antes, status_foun=CANCELED, nota=nota)
	url = reverse('kazu-detail', args=[kazu.pk])
	msg = lambda: _('Kazu %(k)s kansela automátiku: loron %(n)s %(r)s.') % {'k': kazu.kode or kazu.kode_hp or '', 'n': LORON, 'r': _razaun(antes)}
	for u in {kazu.created_by, kazu.followup_ba} - {None}:
		if u.is_active:
			transaction.on_commit(lambda u=u: kirim_notif(u, 'KAZU_STATUS', msg, url=url, email=True))
	logger.warning(f'Limpeza: kazu {kazu.kode or kazu.pk} kansela automátiku ({antes}, loron {LORON})')


# hamoos kazu ida permanente + file evidénsia (foto / vídeo / dokumentu)
def _hamoos(kazu):
	kode = kazu.kode or kazu.kode_hp or str(kazu.pk)
	files = [e.file for e in kazu.evidensia.all() if e.file]
	try:
		with transaction.atomic():
			kazu.delete()
	except ProtectedError:
		logger.warning(f'Limpeza: kazu {kode} la hamoos (iha dadus legál)')
		return False
	for f in files:
		try:
			f.storage.delete(f.name)
		except OSError:
			logger.warning(f'Limpeza: file {f.name} la bele hamoos')
	logger.warning(f'Limpeza: kazu {kode} hamoos permanente (kansela automátiku loron {LORON} liu)')
	return True


# knaar kada loron: kansela, hamoos no lembrete. Retorna totál ba log / komandu.
# simula=True: la muda buat ida, retorna lista kódigu de'it (pratinjau ba Admin)
def hala_o(agora=None, simula=False):
	agora = agora or timezone.now()
	rez = {'kansela': 0, 'hamoos': 0, 'lembrete': 0}
	if simula:
		rez.update(lista_kansela=[], lista_hamoos=[], lista_tuir_mai=[])
	if not settings.LIMPEZA_ATIVU and not simula:
		return rez
	baze = _baze()
	lembra = {SYNCED: {}, VERIFIED: {}}                    # {status: {loron_restu: n}}
	for kazu in baze.filter(status__in=list(REGRA)).select_related('created_by', 'followup_ba'):
		dias = loron_hein(kazu, agora)
		if simula:
			if dias >= LORON:
				rez['lista_kansela'].append(f'{kazu.kode or kazu.kode_hp} ({kazu.status}, loron {dias})')
			elif dias >= LEMBRA[0]:
				rez['lista_tuir_mai'].append(f'{kazu.kode or kazu.kode_hp} ({kazu.status}, kansela iha loron {LORON - dias})')
			continue
		if dias >= LORON:
			_kansela(kazu, agora)
			rez['kansela'] += 1
		elif dias in LEMBRA:
			lembra[kazu.status][LORON - dias] = lembra[kazu.status].get(LORON - dias, 0) + 1
	if simula:
		for kazu in baze.filter(status=CANCELED, kansela_auto_iha__isnull=False):
			if (agora - kazu.kansela_auto_iha).days >= LORON:
				rez['lista_hamoos'].append(kazu.kode or kazu.kode_hp or str(kazu.pk))
		rez['kansela'], rez['hamoos'] = len(rez['lista_kansela']), len(rez['lista_hamoos'])
		return rez
	for status, por_loron in lembra.items():
		papel = REGRA[status][1]
		for restu, n in por_loron.items():
			msg = lambda n=n, restu=restu, status=status: _('Kazu %(n)s %(r)s seidauk: sei kansela automátiku iha loron %(d)s.') % {'n': n, 'r': _razaun(status), 'd': restu}
			kirim_notif_role(papel, 'SISTEMA', msg, url=reverse('kazu-list') + f'?status={status}', urgent=restu <= 2, email=True)
			rez['lembrete'] += 1
	n_lembra = 0
	for kazu in baze.filter(status=CANCELED, kansela_auto_iha__isnull=False):
		dias = (agora - kazu.kansela_auto_iha).days
		if dias >= LORON:
			rez['hamoos'] += int(_hamoos(kazu))
		elif dias == LEMBRA_HAMOOS:
			n_lembra += 1
	if n_lembra:
		msg = lambda: _('Kazu %(n)s kansela automátiku sei hamoos permanente iha loron %(d)s. Restaura se presiza.') % {'n': n_lembra, 'd': LORON - LEMBRA_HAMOOS}
		kirim_notif_role(ROLE_REJEITA, 'SISTEMA', msg, url=reverse('kazu-list') + f'?status={CANCELED}', urgent=True, email=True)
		rez['lembrete'] += 1
	return rez


# data kazu kansela automátiku sei hamoos permanente (ba hatudu iha detalla)
def data_hamoos(kazu):
	if kazu.status != CANCELED or not kazu.kansela_auto_iha:
		return None
	return timezone.localtime(kazu.kansela_auto_iha + timedelta(days=LORON)).date()


# Admin / Superadmin restaura kazu kansela automátiku → status uluk; konta loron 30 hahú fali
@transaction.atomic
def restaura(kazu, user):
	if c_user_group(user) not in ROLE_REJEITA:
		raise PermissionDenied
	kazu = Kazu.objects.select_for_update().get(pk=kazu.pk)
	if kazu.status != CANCELED or not kazu.kansela_auto_iha or kazu.kansela_auto_antes not in REGRA:
		raise ValidationError(_('Kazu ne\'e la kansela automátiku.'))
	agora = timezone.now()
	antes = kazu.kansela_auto_antes
	setattr(kazu, REGRA[antes][0], agora)                 # loron 30 foun hahú ohin
	kazu.status, kazu.kansela_auto_iha, kazu.kansela_auto_antes = antes, None, ''
	kazu.save(update_fields=['status', REGRA[antes][0], 'kansela_auto_iha', 'kansela_auto_antes'])
	KazuHistoria.objects.create(kazu=kazu, user=user, status_antes=CANCELED, status_foun=antes,
		nota=_('Restaura husi kansela automátiku.'))
	logger.info(f'Limpeza: kazu {kazu.kode or kazu.pk} restaura husi {user.username}')
	return kazu
