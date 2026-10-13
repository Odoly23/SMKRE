from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_SEGIMENTU
from kazu.forms import SegimentuForm, AkompanamentuForm
from kazu.models import Kazu, KazuHistoria, KazuSegimentu
from users.auth_utils import c_user_group


@login_required
@allowed_users(allowed_roles=ROLE_SEGIMENTU)
def KazuSegimentuUpdate(request, uuid):
	# Segimentu kazu (eskritóriu): tribunál, notifikasaun, status rezolusaun, desizaun RbR, fokal point
	group = c_user_group(request.user)
	kazu = get_object_or_404(Kazu, pk=uuid)
	objects, _foun = KazuSegimentu.objects.get_or_create(kazu=kazu)
	if request.method == 'POST':
		form = SegimentuForm(request.POST, instance=objects)
		if form.is_valid():
			instance = form.save(commit=False)
			instance.updated_by = request.user
			instance.save()
			if form.changed_data:
				KazuHistoria.objects.create(kazu=kazu, user=request.user, tipu=KazuHistoria.EDITA,
					status_foun=kazu.status, nota=_('Segimentu atualiza: %(c)s') % {'c': ', '.join(str(form.fields[c].label) for c in form.changed_data)})
			messages.success(request, _('Segimentu kazu rai ona.'))
			return redirect('kazu-detail', uuid=uuid)
	else:
		form = SegimentuForm(instance=objects)
	context = {
		'group': group, "page": "kazu",
		'form': form, 'kazu': kazu,
		'link_antes': [{'link_name': 'kazu-list', 'link_text': _('Kazu')}, {'link_name': 'kazu-detail', 'link_param': kazu.pk, 'link_text': str(kazu)}],
		'title': _('Segimentu Kazu'), 'legend': _('Segimentu Kazu')
	}
	return render(request, 'kazu/segimentu_form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_SEGIMENTU)
@require_POST
def KazuAkompanamentuAdd(request, uuid):
	# Aumenta rejistu akompañamentu (data + asaun) iha detalla kazu
	kazu = get_object_or_404(Kazu, pk=uuid)
	form = AkompanamentuForm(request.POST)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.kazu, instance.created_by = kazu, request.user
		instance.save()
		messages.success(request, _('Akompañamentu aumenta ona.'))
	else:
		messages.error(request, ' '.join(e for errs in form.errors.values() for e in errs))
	return redirect('kazu-detail', uuid=uuid)
