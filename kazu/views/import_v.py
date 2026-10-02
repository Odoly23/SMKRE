from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _, gettext_lazy as _l
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_IMPORT_KAZU
from kazu.forms import ImportForm, LokasaunForm
from kazu.importa import template_excel, kria_pratinjau, konfirma, pode_muda_lokasaun, muda_lokasaun
from kazu.models import Kazu, KazuImport
from users.auth_utils import c_user_group

LINK_IMPORT = [{"link_name": "kazu-import", "link_text": _l("Import Kazu")}]


@login_required
@allowed_users(allowed_roles=ROLE_IMPORT_KAZU)
def KazuImportList(request):
	# Upload Excel + istória import
	group = c_user_group(request.user)
	if request.method == 'POST':
		form = ImportForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				imp = kria_pratinjau(form.cleaned_data['file'], request.user)
				if KazuImport.objects.filter(sha256=imp.sha256, status=KazuImport.REMATA).exists():
					messages.warning(request, _('File ne\'e import ona uluk. Haree didi\'ak molok konfirma (risku duplikadu).'))
				return redirect('kazu-import-detail', uuid=imp.pk)
			except ValidationError as e:
				messages.error(request, ' '.join(e.messages))
	else:
		form = ImportForm()
	context = {
		'group': group, "page": "import",
		'form': form, 'objects': KazuImport.objects.select_related('created_by')[:30],
		'title': _('Import Kazu'), 'legend': _('Import Kazu husi Excel')
	}
	return render(request, 'kazu/import_list.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_IMPORT_KAZU)
def KazuImportTemplate(request):
	response = HttpResponse(template_excel(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = 'attachment; filename="SMKRE_template_import_kazu.xlsx"'
	return response


@login_required
@allowed_users(allowed_roles=ROLE_IMPORT_KAZU)
def KazuImportDetail(request, uuid):
	# Pratinjau (molok konfirma) ka rezultadu (hafoin konfirma)
	group = c_user_group(request.user)
	objects = get_object_or_404(KazuImport, pk=uuid)
	kazu_list = objects.kazu_set.select_related('munisipiu', 'suku').order_by('kode') if objects.status == KazuImport.REMATA else []
	# Pontu ba mapa: pratinjau (liña válidu) ka kazu ne'ebé kria ona (fatin atuál)
	if kazu_list:
		pontu = [{'lat': float(k.latitude), 'lng': float(k.longitude), 'aprox': k.gps_aproksimadu, 'titulu': k.kode,
			'sub': ', '.join(x for x in (k.suku.name if k.suku else '', k.munisipiu.name) if x),
			'url': reverse('kazu-lokasaun', args=[k.pk]) if pode_muda_lokasaun(k) else reverse('kazu-detail', args=[k.pk])} for k in kazu_list]
	else:
		pontu = [{'lat': float(r['dadus']['latitude']), 'lng': float(r['dadus']['longitude']), 'aprox': r['dadus']['gps_aproksimadu'],
			'titulu': _('Liña %(n)s') % {'n': r['lina']}, 'sub': r['rezumu']['munisipiu'], 'url': ''}
			for r in objects.dadus if r['ok'] and r['dadus']['latitude']]
	context = {
		'group': group, "page": "import",
		'objects': objects, 'lina': objects.dadus, 'pontu': pontu,
		'kazu_list': kazu_list,
		'link_antes': LINK_IMPORT,
		'title': objects.naran_file, 'legend': _('Pratinjau Import')
	}
	return render(request, 'kazu/import_detail.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_IMPORT_KAZU)
@require_POST
def KazuImportKonfirma(request, uuid):
	objects = get_object_or_404(KazuImport, pk=uuid)
	try:
		n = konfirma(objects, request.user)
		messages.success(request, _('Kazu %(n)s import ona ho status "Hein Verifikasaun".') % {'n': n})
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	return redirect('kazu-import-detail', uuid=uuid)


@login_required
@allowed_users(allowed_roles=ROLE_IMPORT_KAZU)
@require_POST
def KazuImportKansela(request, uuid):
	objects = get_object_or_404(KazuImport, pk=uuid, status=KazuImport.RASCUNHO)
	objects.status = KazuImport.KANSELA
	objects.save(update_fields=['status'])
	messages.info(request, _('Import kansela. La iha kazu ida kria.'))
	return redirect('kazu-import')


@login_required
@allowed_users(allowed_roles=ROLE_IMPORT_KAZU)
def KazuLokasaun(request, uuid):
	# Hadia fatin kazu iha mapa: dada marka ka klik iha mapa (molok aprova)
	group = c_user_group(request.user)
	objects = get_object_or_404(Kazu.objects.select_related('munisipiu', 'postu', 'suku'), pk=uuid)
	if not pode_muda_lokasaun(objects):
		messages.error(request, _('Lokasaun bele muda deit molok kazu aprova.'))
		return redirect('kazu-detail', uuid=uuid)
	if request.method == 'POST':
		form = LokasaunForm(request.POST)
		if form.is_valid():
			try:
				muda_lokasaun(objects, request.user, form.cleaned_data['latitude'], form.cleaned_data['longitude'])
				messages.success(request, _('Lokasaun kazu %(kode)s rai ona.') % {'kode': objects.kode})
				return redirect('kazu-detail', uuid=uuid)
			except ValidationError as e:
				messages.error(request, ' '.join(e.messages))
	else:
		form = LokasaunForm(initial={'latitude': objects.latitude, 'longitude': objects.longitude})
	context = {
		'group': group, "page": "kazu",
		'objects': objects, 'form': form,
		'link_antes': [{'link_name': 'kazu-list', 'link_text': _('Kazu')}, {'link_name': 'kazu-detail', 'link_param': objects.pk, 'link_text': objects.kode}],
		'title': _('Hadia lokasaun'), 'legend': _('Hadia lokasaun kazu')
	}
	return render(request, 'kazu/lokasaun.html', context)
