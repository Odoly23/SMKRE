from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_LEGAL, ROLE_LEGAL_EDIT
from kazu.models import Kazu
from legal.forms import DokumentuForm, VersaunForm
from legal.models import DokumentuLegal, AsesuVault
from legal.services import dokumentu_queryset, can_download, can_edit_vault, upload_dokumentu, versaun_foun, \
	arkiva_dokumentu, rejista_asesu, KAZU_STATUS_LEGAL


def _dokumentu_ka_404(request, pk):
	doc = get_object_or_404(DokumentuLegal.objects.select_related('kazu'), pk=pk)
	if not can_download(request.user, doc):
		raise Http404            # konfidensiál: la hatudu katak iha
	return doc


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL)
def legalVault(request):
	group = request.user.groups.all()[0].name
	objects = dokumentu_queryset(request.user)
	q = request.GET.get('q', '').strip()
	kategoria = request.GET.get('kategoria', '')
	if q:
		objects = objects.filter(Q(titulu__icontains=q) | Q(kazu__kode__icontains=q) | Q(deskrisaun__icontains=q))
	if kategoria:
		objects = objects.filter(kategoria=kategoria)
	if request.GET.get('jeral'):
		objects = objects.filter(kazu=None)
	objects = Paginator(objects, 25).get_page(request.GET.get('page'))
	context = {
		'group': group, "page": "legal",
		'objects': objects, 'q': q, 'f_kategoria': kategoria,
		'kategoria_choices': DokumentuLegal.KATEGORIA_CHOICES, 'can_edit': can_edit_vault(request.user),
		'title': _('Document Vault'), 'legend': _('Document Vault Legál')
	}
	return render(request, 'legal/vault.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL)
def DokumentuDetail(request, pk):
	group = request.user.groups.all()[0].name
	objects = _dokumentu_ka_404(request, pk)
	context = {
		'group': group, "page": "legal",
		'objects': objects, 'versaun': objects.historia_versaun(),
		'asesu': AsesuVault.objects.filter(dokumentu__in=objects.historia_versaun()).select_related('user__pesoaluser__pesoal')[:50],
		'can_edit': can_edit_vault(request.user),
		'title': objects.titulu, 'legend': _('Detalla Dokumentu')
	}
	return render(request, 'legal/dokumentu_detail.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_EDIT)
def DokumentuAdd(request, uuid=None):
	group = request.user.groups.all()[0].name
	kazu = get_object_or_404(Kazu, pk=uuid, status__in=KAZU_STATUS_LEGAL) if uuid else None
	if request.method == 'POST':
		form = DokumentuForm(request.POST, request.FILES, kazu=kazu)
		if form.is_valid():
			instance = form.save(commit=False)
			try:
				instance = upload_dokumentu(request, instance, request.FILES['file'])
				messages.success(request, _('Dokumentu rai ona iha vault.'))
				return redirect('legal-kazu', uuid=instance.kazu_id) if instance.kazu_id else redirect('legal-dok-detail', pk=instance.pk)
			except ValidationError as e:
				form.add_error('file', ' '.join(e.messages))
	else:
		form = DokumentuForm(kazu=kazu)
	context = {
		'group': group, "page": "legal",
		'form': form, 'kazu': kazu,
		'title': _('Aumenta Dokumentu'), 'legend': _('Aumenta Dokumentu Legál')
	}
	return render(request, 'legal/dokumentu_form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_EDIT)
def DokumentuVersaun(request, pk):
	group = request.user.groups.all()[0].name
	antes = _dokumentu_ka_404(request, pk)
	if request.method == 'POST':
		form = VersaunForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				doc = versaun_foun(request, antes, request.FILES['file'], form.cleaned_data['deskrisaun'])
				messages.success(request, _('Versaun %(v)s rai ona.') % {'v': doc.versaun})
				return redirect('legal-dok-detail', pk=doc.pk)
			except ValidationError as e:
				form.add_error('file', ' '.join(e.messages))
	else:
		form = VersaunForm()
	context = {
		'group': group, "page": "legal",
		'form': form, 'objects': antes,
		'title': _('Versaun Foun'), 'legend': _('Versaun Foun Dokumentu')
	}
	return render(request, 'legal/versaun_form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL)
def DokumentuDownload(request, pk):
	# File vault LA iha /media/: download liuhusi ne'e deit (login + papél + rejistu asesu)
	doc = _dokumentu_ka_404(request, pk)
	try:
		f = doc.file.open('rb')
	except (FileNotFoundError, ValueError):
		raise Http404
	rejista_asesu(request, doc, AsesuVault.DOWNLOAD)
	naran = f'{slugify(doc.titulu)[:60] or "dokumentu"}-v{doc.versaun}.{doc.ext}'
	response = FileResponse(f, as_attachment=True, filename=naran)
	response['Cache-Control'] = 'private, no-store'
	response['X-Content-Type-Options'] = 'nosniff'
	return response


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_EDIT)
@require_POST
def DokumentuArkivu(request, pk):
	doc = _dokumentu_ka_404(request, pk)
	try:
		arkiva_dokumentu(request, doc, request.POST.get('razaun', ''))
		messages.warning(request, _('Dokumentu arkiva ona.'))
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
		return redirect('legal-dok-detail', pk=pk)
	except PermissionDenied:
		return render(request, 'home/403.html', status=403)
	return redirect('legal-kazu', uuid=doc.kazu_id) if doc.kazu_id else redirect('legal-vault')
