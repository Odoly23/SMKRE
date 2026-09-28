from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_LEGAL_EDIT
from kazu.models import Kazu
from legal.forms import NotaForm
from legal.models import NotaLegal
from legal.services import KAZU_STATUS_LEGAL


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_EDIT)
def NotaAdd(request, uuid):
	group = request.user.groups.all()[0].name
	kazu = get_object_or_404(Kazu, pk=uuid, status__in=KAZU_STATUS_LEGAL)
	if request.method == 'POST':
		form = NotaForm(request.POST)
		if form.is_valid():
			instance = form.save(commit=False)
			instance.kazu = kazu
			instance.created_by = request.user
			instance.save()
			messages.success(request, _('Nota legál rai ona.'))
			return redirect('legal-kazu', uuid=uuid)
	else:
		form = NotaForm()
	context = {
		'group': group, "page": "legal",
		'form': form, 'kazu': kazu,
		'title': _('Nota Legál'), 'legend': _('Aumenta Nota Legál')
	}
	return render(request, 'legal/nota_form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_EDIT)
def NotaUpdate(request, pk):
	group = request.user.groups.all()[0].name
	objects = get_object_or_404(NotaLegal.objects.select_related('kazu'), pk=pk)
	if request.method == 'POST':
		form = NotaForm(request.POST, instance=objects)
		if form.is_valid():
			form.save()
			messages.success(request, _('Nota legál atualiza ona.'))
			return redirect('legal-kazu', uuid=objects.kazu_id)
	else:
		form = NotaForm(instance=objects)
	context = {
		'group': group, "page": "legal",
		'form': form, 'kazu': objects.kazu, 'objects': objects,
		'title': _('Nota Legál'), 'legend': _('Edita Nota Legál')
	}
	return render(request, 'legal/nota_form.html', context)
