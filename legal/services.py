"""
Regra Document Vault (fatin IDA deit).

	Upload    → valida tipu file tuir konteúdu (la fiar extensaun deit) + SHA-256 + rejistu asesu
	Versaun   → dokumentu foun troka versaun atuál; versaun tuan hela (la hamoos) ba istória
	Arkivu    → la hamoos: dokumentu subar husi lista, hela ba auditoria
	Download  → Ofisiál Legál / Superadmin / papél legál; konfidensiál = ROLE_LEGAL_EDIT deit
"""
import hashlib
import logging
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from config.rbac import ROLE_LEGAL, ROLE_LEGAL_EDIT, OFISIAL_LEGAL, SUPERADMIN
from config.utils import get_client_ip
from legal.models import DokumentuLegal, NotaLegal, AsesuVault
from notification.utils import kirim_notif_role
from users.auth_utils import c_user_group

logger = logging.getLogger('smkre.seguransa')

VAULT_MAX_MB = 20
# extensaun: bytes hahú (magic) — file tenke loos tuir konteúdu
VAULT_TIPU = {
	'pdf': (b'%PDF',),
	'jpg': (b'\xff\xd8\xff',),
	'jpeg': (b'\xff\xd8\xff',),
	'png': (b'\x89PNG\r\n\x1a\n',),
	'docx': (b'PK\x03\x04',),
}
KAZU_STATUS_LEGAL = ('VERIFIED', 'APPROVED', 'COMPLETED')   # kazu tenke verifika uluk


# ── Asesu ──
def can_view_vault(user):
	return c_user_group(user) in ROLE_LEGAL


def can_edit_vault(user):
	return c_user_group(user) in ROLE_LEGAL_EDIT


def dokumentu_queryset(user):
	# Dokumentu atuál, la arkivadu; konfidensiál ba ROLE_LEGAL_EDIT deit
	qs = DokumentuLegal.objects.filter(atual=True, arkivadu=False).select_related('kazu', 'uploaded_by__pesoaluser__pesoal')
	if not can_view_vault(user):
		return qs.none()
	if not can_edit_vault(user):
		qs = qs.filter(konfidensial=False)
	return qs


def nota_queryset(user, kazu):
	qs = NotaLegal.objects.filter(kazu=kazu).select_related('created_by__pesoaluser__pesoal')
	if not can_edit_vault(user):
		qs = qs.filter(konfidensial=False)
	return qs


def can_download(user, doc):
	if not can_view_vault(user):
		return False
	return not doc.konfidensial or can_edit_vault(user)


def rejista_asesu(request, doc, aksaun):
	AsesuVault.objects.create(dokumentu=doc, user=request.user, aksaun=aksaun, ip=get_client_ip(request))
	logger.info(f'Vault {aksaun}: {doc.pk} "{doc.titulu}" husi {request.user.username}')


# ── File ──
def valida_file(f):
	# Tipu file tuir extensaun NO konteúdu (magic bytes) + tamañu máximu
	naran = f.name or ''
	ext = naran.rsplit('.', 1)[-1].lower() if '.' in naran else ''
	if ext not in VAULT_TIPU:
		raise ValidationError(_('Formatu file la permite. Uza: %(ext)s') % {'ext': 'PDF, JPG, PNG, DOCX'})
	if f.size > VAULT_MAX_MB * 1024 * 1024:
		raise ValidationError(_('File boot liu. Máximu %(mb)s MB.') % {'mb': VAULT_MAX_MB})
	f.seek(0)
	inisiu = f.read(16)
	f.seek(0)
	if not any(inisiu.startswith(m) for m in VAULT_TIPU[ext]):
		raise ValidationError(_("Konteúdu file la hanesan ho extensaun (.%(ext)s). File bele estraga ka falsu.") % {'ext': ext})
	return ext


def sha256_file(f):
	h = hashlib.sha256()
	f.seek(0)
	for pedasu in f.chunks() if hasattr(f, 'chunks') else iter(lambda: f.read(65536), b''):
		h.update(pedasu)
	f.seek(0)
	return h.hexdigest()


def _prenxe_file(doc, f):
	doc.naran_orijinal = (f.name or '')[-200:]
	doc.tamanu = f.size
	doc.sha256 = sha256_file(f)


# ── Aksaun ──
@transaction.atomic
def upload_dokumentu(request, doc, f):
	# doc = DokumentuLegal (seidauk rai) husi formuláriu
	if not can_edit_vault(request.user):
		raise PermissionDenied
	if doc.kazu_id and doc.kazu.status not in KAZU_STATUS_LEGAL:
		raise ValidationError(_('Kazu tenke verifika uluk.'))
	valida_file(f)
	_prenxe_file(doc, f)
	doc.file = f
	doc.uploaded_by = request.user
	doc.save()
	rejista_asesu(request, doc, AsesuVault.UPLOAD)
	return doc


@transaction.atomic
def versaun_foun(request, antes, f, deskrisaun=''):
	# Versaun foun ba dokumentu ida: kopia metadata, troka file, versaun tuan sai la atuál
	if not can_edit_vault(request.user):
		raise PermissionDenied
	antes = DokumentuLegal.objects.select_for_update().get(pk=antes.pk)
	if not antes.atual or antes.arkivadu:
		raise ValidationError(_('Dokumentu ne\'e la atuál.'))
	valida_file(f)
	doc = DokumentuLegal(kazu=antes.kazu, kategoria=antes.kategoria, titulu=antes.titulu,
		deskrisaun=deskrisaun or antes.deskrisaun, data_dokumentu=antes.data_dokumentu, konfidensial=antes.konfidensial,
		versaun=antes.versaun + 1, versaun_anterior=antes, uploaded_by=request.user)
	_prenxe_file(doc, f)
	doc.file = f
	antes.atual = False
	antes.save(update_fields=['atual'])
	doc.save()
	rejista_asesu(request, doc, AsesuVault.VERSAUN)
	return doc


@transaction.atomic
def arkiva_dokumentu(request, doc, razaun):
	if not can_edit_vault(request.user):
		raise PermissionDenied
	razaun = (razaun or '').strip()
	if len(razaun) < 5:
		raise ValidationError(_('Favor hakerek razaun (minimu karakter 5).'))
	doc.arkivadu, doc.arkivu_razaun, doc.arkivu_by, doc.arkivu_at = True, razaun[:255], request.user, timezone.now()
	doc.save(update_fields=['arkivadu', 'arkivu_razaun', 'arkivu_by', 'arkivu_at'])
	rejista_asesu(request, doc, AsesuVault.ARKIVU)
	return doc


def notifika_aksaun_legal(kazu, actor):
	# Status kazu → Aksaun Legál: equipa legál simu notifikasaun
	from django.urls import reverse
	msg = lambda: _('Kazu %(kode)s tama faze Aksaun Legál.') % {'kode': kazu.kode}
	transaction.on_commit(lambda: kirim_notif_role([OFISIAL_LEGAL, SUPERADMIN], 'LEGAL', msg,
		url=reverse('legal-kazu', args=[kazu.pk]), actor=actor, email=True))
