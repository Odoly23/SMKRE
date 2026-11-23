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


# dadus ne'ebé utilizador ida kria (PROTECT): la bele hamoos utilizador se iha
def dadus_utilizador(u):
	from kazu.models import Kazu
	from kazu.models.importa import KazuImport
	from legal.models import SurveiLegal
	return {
		_('kazu'): Kazu.objects.filter(created_by=u).count(),
		_('survei legál'): SurveiLegal.objects.filter(created_by=u).count(),
		_('import Excel'): KazuImport.objects.filter(created_by=u).count(),
	}


# Utilizador: hamoos konta (User) + dadus pesoál (Pesoal, foto). Labele: an rasik, Superadmin ikus,
# ka utilizador ne'ebé kria ona kazu / survei / import (dadus sei lakon autór) → hapara konta deit.
@transaction.atomic
def hamoos_utilizador(pesoal, user):
	from django.core.exceptions import ValidationError
	from config.rbac import SUPERADMIN
	from django.contrib.auth.models import User
	alvu = getattr(getattr(pesoal, 'pesoaluser', None), 'user', None)
	if alvu and alvu.pk == user.pk:
		raise ValidationError(_('Labele hamoos ita-nia konta rasik.'))
	if alvu and alvu.groups.filter(name=SUPERADMIN).exists() and \
			User.objects.filter(groups__name=SUPERADMIN, is_active=True).exclude(pk=alvu.pk).count() == 0:
		raise ValidationError(_('Labele hamoos Superadmin ikus.'))
	if alvu:
		iha = {k: n for k, n in dadus_utilizador(alvu).items() if n}
		if iha:
			lista = ', '.join(f'{n} {k}' for k, n in iha.items())
			raise ValidationError(_('Utilizador ne\'e kria ona %(l)s. Labele hamoos (dadus sei lakon autór) — HAPARA konta deit.') % {'l': lista})
	naran = str(pesoal)
	files = [f for f in (getattr(pesoal, 'image', None),) if f]
	if alvu:
		alvu.delete()                                 # PesoalUser, autorizasaun offline, notifikasaun (CASCADE)
	pesoal.delete()
	_hamoos_file(files)
	_log(user, f'utilizador {naran}')
	return naran
