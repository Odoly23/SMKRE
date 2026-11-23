"""Hamoos dadus permanente — Superadmin DE'IT (config.rbac.ROLE_HAMOOS).
Kada funsaun: hamoos rejistu + file iha disku (foto, PDF, dokumentu) no rejista iha log seguransa.
Labele fila fali (la iha lixeira) — view husu konfirmasaun uluk."""
import logging
from django.db import transaction
from django.utils.translation import gettext as _

logger = logging.getLogger('smkre.seguransa')


# hamoos file iha disku hafoin database commit (se commit falla, file la lakon)
def _hamoos_file(files):
	def hamoos():
		for f in files:
			try:
				f.storage.delete(f.name)
			except OSError:
				logger.warning('Hamoos: file %s la bele hamoos', f.name)
	transaction.on_commit(hamoos)


def _log(user, testu):
	logger.warning('HAMOOS husi %s: %s', getattr(user, 'username', '?'), testu)


# versaun hotu dokumentu ida (tuan → foun): hamoos hamutuk
def _versaun_hotu(dok):
	from legal.models import DokumentuLegal
	while dok.versaun_anterior_id:
		dok = dok.versaun_anterior
	lista = [dok]
	while True:
		foun = DokumentuLegal.objects.filter(versaun_anterior=lista[-1]).first()
		if not foun:
			return lista
		lista.append(foun)


def _hamoos_dokumentu_lista(docs):
	files = [d.file for d in docs if d.file]
	for d in reversed(docs):                          # foun uluk (versaun_anterior PROTECT)
		d.asesu.all().delete()
		d.delete()
	return files


# Kazu: evidénsia, istória, afetadu… (CASCADE) + nota / dokumentu legál kazu nian.
# Survei legál ne'ebé liga ba kazu la hamoos — liga deit kotu (survei hela).
@transaction.atomic
def hamoos_kazu(kazu, user):
	from legal.models import DokumentuLegal
	kode = kazu.kode or kazu.kode_hp or str(kazu.pk)
	files = [e.file for e in kazu.evidensia.all() if e.file]
	kazu.survei_legal.update(kazu=None)
	kazu.nota_legal.all().delete()
	vistu = set()
	for d in DokumentuLegal.objects.filter(kazu=kazu):
		if d.pk in vistu:
			continue
		lista = _versaun_hotu(d)
		vistu.update(x.pk for x in lista)
		files += _hamoos_dokumentu_lista(lista)
	kazu.delete()
	_hamoos_file(files)
	_log(user, f'kazu {kode}')
	return kode


@transaction.atomic
def hamoos_survei(survei, user):
	kode = survei.kode or str(survei.pk)
	files = [f.file for f in survei.files.all() if f.file]
	survei.delete()
	_hamoos_file(files)
	_log(user, f'survei legál {kode}')
	return kode


@transaction.atomic
def hamoos_dokumentu(dok, user):
	naran = str(dok)
	_hamoos_file(_hamoos_dokumentu_lista(_versaun_hotu(dok)))
	_log(user, f'dokumentu legál {naran}')
	return naran


@transaction.atomic
def hamoos_publikasaun(pub, user):
	naran = str(pub)
	files = [f for f in (getattr(pub, 'file', None),) if f]
	pub.delete()
	_hamoos_file(files)
	_log(user, f'publikasaun {naran}')
	return naran


# Utilizador: hamoos konta (User) + dadus pesoál (Pesoal, foto). Labele: an rasik ka Superadmin ikus.
# Kazu / survei legál / import ne'ebé nia kria MUDA ba Superadmin ne'ebé hamoos (dadus la lakon),
# ho nota iha istória kazu.
@transaction.atomic
def hamoos_utilizador(pesoal, user):
	from django.core.exceptions import ValidationError
	from config.rbac import SUPERADMIN
	from django.contrib.auth.models import User
	from kazu.models import Kazu, KazuHistoria
	from kazu.models.importa import KazuImport
	from legal.models import SurveiLegal
	alvu = getattr(getattr(pesoal, 'pesoaluser', None), 'user', None)
	if alvu and alvu.pk == user.pk:
		raise ValidationError(_('Labele hamoos ita-nia konta rasik.'))
	if alvu and alvu.groups.filter(name=SUPERADMIN).exists() and \
			User.objects.filter(groups__name=SUPERADMIN, is_active=True).exclude(pk=alvu.pk).count() == 0:
		raise ValidationError(_('Labele hamoos Superadmin ikus.'))
	naran = str(pesoal)
	muda = {}
	if alvu:
		kazu = Kazu.objects.filter(created_by=alvu)
		nota = _('Utilizador %(u)s hamoos ona: kazu muda ba %(s)s.') % {'u': naran, 's': user.username}
		KazuHistoria.objects.bulk_create([KazuHistoria(kazu_id=pk, user=user, status_antes=st, status_foun=st, nota=nota)
			for pk, st in kazu.values_list('pk', 'status')])
		muda = {
			_('kazu'): kazu.update(created_by=user),
			_('follow-up'): Kazu.objects.filter(followup_ba=alvu).update(followup_ba=user),
			_('survei legál'): SurveiLegal.objects.filter(created_by=alvu).update(created_by=user),
			_('import Excel'): KazuImport.objects.filter(created_by=alvu).update(created_by=user),
		}
	files = [f for f in (getattr(pesoal, 'image', None),) if f]
	if alvu:
		alvu.delete()                                 # PesoalUser, autorizasaun offline, notifikasaun (CASCADE)
	pesoal.delete()
	_hamoos_file(files)
	lista = ', '.join(f'{n} {k}' for k, n in muda.items() if n)
	_log(user, f'utilizador {naran}' + (f' (muda ba {user.username}: {lista})' if lista else ''))
	return naran + (' — ' + _('muda ba ita: %(l)s') % {'l': lista} if lista else '')
