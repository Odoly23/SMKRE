"""Survei legál (Perguntas Xave Sira Legal): lista, input (ho autorizasaun Admin), detalla, haruka, verifika, file."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy as _l
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_SURVEI_INPUT, ROLE_SURVEI_HAREE, ROLE_SURVEI_VERIFIKA
from custom.models import Munisipiu
from legal.forms import SurveiLegalForm, SurveiFileForm, SURVEI_GRUPU
from legal.models import SurveiLegal, SurveiLegalFile
from legal.services import valida_file
from legal.survei import survei_queryset, input_ativu, can_edit_survei, haruka, verifika
from users.auth_utils import c_user_group, c_user_offline


def _survei_ka_404(request, pk):
	return get_object_or_404(survei_queryset(request.user).select_related('postu', 'aldeia', 'verified_by__pesoaluser__pesoal'), pk=pk)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_HAREE)
def SurveiList(request):
	objects = survei_queryset(request.user)
	q = request.GET.get('q', '').strip()
	status = request.GET.get('status', '')
	mun = request.GET.get('munisipiu', '')
	if q:
		objects = objects.filter(Q(kode__icontains=q) | Q(titulu__icontains=q) | Q(parte_naran__icontains=q)
			| Q(kazu__kode__icontains=q) | Q(suku__name__icontains=q))
	if status:
		objects = objects.filter(status=status)
	if mun.isdigit():
		objects = objects.filter(munisipiu_id=mun)
	if request.GET.get('mine'):
		objects = objects.filter(created_by=request.user)
	objects = Paginator(objects, 25).get_page(request.GET.get('page'))
	context = {
		"page": "legal-survei", 'objects': objects, 'q': q, 'f_status': status, 'f_munisipiu': mun,
		'status_choices': SurveiLegal.STATUS_CHOICES, 'munisipiu_list': Munisipiu.active.all(),
		'input_ativu': input_ativu(request.user), 'autorizasaun': c_user_offline(request.user),
		'is_input_role': c_user_group(request.user) in ROLE_SURVEI_INPUT,
		'title': _('Survei Legál'), 'legend': _('Survei Legál')
	}
	return render(request, 'legal/survei_list.html', context)


def _form(request, instance=None):
	if not input_ativu(request.user):
		messages.error(request, _('Autorizasaun input legál la ativu. Kontaktu Admin.'))
		return redirect('legal-survei-list')
	if instance is not None and not can_edit_survei(request.user, instance):
		raise PermissionDenied
	form = SurveiLegalForm(request.POST or None, instance=instance)
	if request.method == 'POST' and form.is_valid():
		obj = form.save(commit=False)
		if not obj.created_by_id:
			obj.created_by = request.user
		obj.save()
		if request.POST.get('aksaun') == 'haruka':
			try:
				haruka(obj, request.user)
				messages.success(request, _('Survei manda ba server: hein verifikasaun Admin.'))
				return redirect('legal-survei-detail', pk=obj.pk)
			except ValidationError as e:
				messages.error(request, ' '.join(e.messages))
				return redirect('legal-survei-update', pk=obj.pk)
		messages.success(request, _('Survei rai ona (rascunho).'))
		return redirect('legal-survei-detail', pk=obj.pk)
	context = {
		"page": "legal-input", 'form': form, 'objects': instance,
		'title': _('Input Legál'), 'legend': _('Edita Survei Legál') if instance else _('Survei Legál Foun')
	}
	return render(request, 'legal/survei_form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_INPUT)
def SurveiAdd(request):
	return _form(request)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_INPUT)
def SurveiUpdate(request, pk):
	return _form(request, _survei_ka_404(request, pk))


SEKSAUN_DETALLA = [
	(_l('I. Identifikasaun Parte Sira (Disputante Sira)'), ['parte_naran', 'parte_sexu', 'parte_data_moris', 'parte_estadu_civil', 'parte_estadu_civil_seluk',
		'parte_hela_fatin', 'parte_kartaun_eleitoral', 'parte_profisaun', 'parte_kontaktu', 'parte_ehd']),
	(_l("II. Entidade ne'ebe atu foti rai"), SURVEI_GRUPU['entidade']),
	(_l('III. Perguntas Xave Sira'), ['meius'] + SURVEI_GRUPU['eransa'] + SURVEI_GRUPU['sosa'] + SURVEI_GRUPU['foo'] + SURVEI_GRUPU['posse']),
]


def _resposta(obj):
	# Seksaun → [(pergunta, resposta)] — resposta mamuk la hatudu
	seksaun = []
	for titulu, kampu in SEKSAUN_DETALLA:
		linha = []
		for c in kampu:
			f = obj._meta.get_field(c)
			v = getattr(obj, f'get_{c}_display')() if f.choices else getattr(obj, c)
			if v in (None, ''):
				continue
			linha.append((f.verbose_name, v.strftime('%d/%m/%Y') if hasattr(v, 'strftime') else v))
		seksaun.append((titulu, linha))
	return seksaun


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_HAREE)
def SurveiDetail(request, pk):
	obj = _survei_ka_404(request, pk)
	can_edit = can_edit_survei(request.user, obj)
	context = {
		"page": "legal-survei", 'objects': obj, 'seksaun': _resposta(obj),
		'notas': [(_('Dokumentus identifikasaun'), obj.label_lista('dok_identifikasaun')),
			(_('Dokumentus relevante sira seluk'), obj.label_lista('dok_relevante')), (_('Fotografia'), obj.label_lista('fotografia'))],
		'files': obj.files.select_related('uploaded_by__pesoaluser__pesoal'),
		'can_edit': can_edit, 'file_form': SurveiFileForm() if can_edit else None,
		'can_verifika': c_user_group(request.user) in ROLE_SURVEI_VERIFIKA and obj.status == SurveiLegal.HARUKA,
		'title': str(obj), 'legend': _('Detalla Survei Legál')
	}
	return render(request, 'legal/survei_detail.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_INPUT)
@require_POST
def SurveiHaruka(request, pk):
	obj = _survei_ka_404(request, pk)
	if not can_edit_survei(request.user, obj):
		raise PermissionDenied
	try:
		haruka(obj, request.user)
		messages.success(request, _('Survei manda ba server: hein verifikasaun Admin.'))
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	return redirect('legal-survei-detail', pk=pk)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_VERIFIKA)
@require_POST
def SurveiVerifika(request, pk):
	obj = _survei_ka_404(request, pk)
	aprova = request.POST.get('aksaun') != 'rejeita'
	try:
		verifika(obj, request.user, aprova=aprova, nota=request.POST.get('nota', ''))
		messages.success(request, _('Survei verifika ona.') if aprova else _('Survei rejeita: haruka fali ba Ofisiál Legál.'))
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	return redirect('legal-survei-detail', pk=pk)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_INPUT)
@require_POST
def SurveiFileAdd(request, pk):
	obj = _survei_ka_404(request, pk)
	if not can_edit_survei(request.user, obj):
		raise PermissionDenied
	form = SurveiFileForm(request.POST, request.FILES)
	if form.is_valid():
		try:
			valida_file(request.FILES['file'])
			f = form.save(commit=False)
			f.survei, f.uploaded_by = obj, request.user
			f.save()
			messages.success(request, _('File upload ona.'))
		except ValidationError as e:
			messages.error(request, ' '.join(e.messages))
	else:
		messages.error(request, ' '.join(m for err in form.errors.values() for m in err))
	return redirect('legal-survei-detail', pk=pk)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_INPUT)
@require_POST
def SurveiFileDelete(request, pk):
	f = get_object_or_404(SurveiLegalFile.objects.select_related('survei'), pk=pk)
	if not can_edit_survei(request.user, f.survei):
		raise PermissionDenied
	survei_id = f.survei_id
	f.file.delete(save=False)
	f.delete()
	messages.warning(request, _('File hamoos ona.'))
	return redirect('legal-survei-detail', pk=survei_id)


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_HAREE)
def SurveiFileDownload(request, pk):
	# File survei la iha /media/ públiku: liuhusi ne'e deit (login + papél)
	f = get_object_or_404(SurveiLegalFile, pk=pk, survei__in=survei_queryset(request.user))
	try:
		fh = f.file.open('rb')
	except (FileNotFoundError, ValueError):
		raise Http404
	ext = f.file.name.rsplit('.', 1)[-1]
	response = FileResponse(fh, as_attachment=not (f.is_image and request.GET.get('inline')),
		filename=f'{slugify(f.naran)[:60] or "survei"}.{ext}')
	response['Cache-Control'] = 'private, no-store'
	response['X-Content-Type-Options'] = 'nosniff'
	return response


# ── PDF survei ida-ida (orden dokumentu "Perguntas Xave Sira Legal" + kop surat) ──
MEIUS_PDF = {
	'ERANSA': (_l('1. Eransa / Antesessor mate ona'), ['eransa_husi_se', 'eransa_relasaun', 'eransa_herdeiru', 'eransa_rai_seluk', 'eransa_fahe',
		('eransa_fahe', 'SIN', ['eransa_fahe_ba_se', 'eransa_fahe_lokalizasaun', 'eransa_fahe_desde'])]),
	'SOSA': (_l('2. Sosa'), ['sosa_husi_se', 'sosa_folin', 'sosa_bainhira', 'sosa_halo_saida', 'sosa_halo_desde', 'sosa_halo_se',
		'sosa_akordu', ('sosa_akordu', 'SIN', ['sosa_akordu_fatin']), 'sosa_sasin', ('sosa_sasin', 'SIN', ['sasin_1', 'sasin_2', 'sasin_3', 'sasin_4'])]),
	'FOO': (_l('3. Foó / doasaun (bele família ka ema seluk)'), ['foo_se', 'foo_bainhira', 'foo_akordu',
		('foo_akordu', 'SIN', ['foo_akordu_fatin']), 'foo_relasaun']),
	'POSSE': (_l('4. Posse / okupa'), SURVEI_GRUPU['posse']),
}


def _linha(obj, kampu):
	# kampu ka (kondisaun, valor, [kampu]) → [(pergunta, resposta, sub)]
	res = []
	for c in kampu:
		if isinstance(c, tuple):
			if getattr(obj, c[0]) == c[1]:
				res += [(l, v, True) for l, v, _s in _linha(obj, c[2])]
			continue
		f = obj._meta.get_field(c)
		v = getattr(obj, f'get_{c}_display')() if f.choices else getattr(obj, c)
		res.append((f.verbose_name, v.strftime('%d/%m/%Y') if hasattr(v, 'strftime') else (v or ''), False))
	return res


@login_required
@allowed_users(allowed_roles=ROLE_SURVEI_HAREE)
def SurveiPDF(request, pk):
	from django.utils import timezone
	from legal.pdf import render_pdf
	obj = _survei_ka_404(request, pk)
	files = {str(f.pk): f for f in obj.files.all() if f.is_image}
	meius = MEIUS_PDF.get(obj.meius)
	lista = lambda campo, choices: [(lbl, k in (getattr(obj, campo) or [])) for k, lbl in choices]
	pesoal = lambda u: getattr(getattr(u, 'pesoaluser', None), 'pesoal', None) or (u.username if u else '')
	context = {
		'obj': obj, 'agora': timezone.localtime(), 'user_naran': pesoal(request.user),
		'parte': _linha(obj, [c if c != 'parte_estadu_civil_seluk' else ('parte_estadu_civil', 'SELUK', [c]) for c in SEKSAUN_DETALLA[0][1]]), 'entidade': _linha(obj, SURVEI_GRUPU['entidade']),
		'meius_opsaun': [(lbl, k == obj.meius) for k, lbl in SurveiLegal.MEIUS_CHOICES],
		'meius_titulu': meius[0] if meius else '', 'meius_linha': _linha(obj, meius[1]) if meius else [],
		'notas': [(_('Dokumentus identifikasaun'), lista('dok_identifikasaun', SurveiLegal.DOK_IDENTIFIKASAUN)),
			(_('Dokumentus relevante sira seluk'), lista('dok_relevante', SurveiLegal.DOK_RELEVANTE)),
			(_('Fotografia'), lista('fotografia', SurveiLegal.FOTOGRAFIA))],
		'fotos': [(pk_, f) for pk_, f in files.items()],
	}
	return render_pdf('legal/survei_pdf.html', context, slugify(obj.kode or f'survei-{str(obj.pk)[:8]}'), files)
