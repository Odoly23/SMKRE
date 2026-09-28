from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_POLICY_KRIA, ROLE_POLICY_PUBLIKA
from publiku.forms import PublikasaunForm
from publiku.models import Publikasaun
from users.auth_utils import c_user_group


@login_required
@allowed_users(allowed_roles=ROLE_POLICY_KRIA)
def PublikasaunList(request):
	group = request.user.groups.all()[0].name
	context = {
		'group': group, "page": "publikasaun",
		'objects': Publikasaun.objects.select_related('created_by__pesoaluser__pesoal'),
		'can_publika': group in ROLE_POLICY_PUBLIKA,
		'title': _('Publikasaun'), 'legend': _('Publikasaun (Policy Brief)')
	}
	return render(request, 'publiku/publikasaun_list.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_POLICY_KRIA)
def PublikasaunAdd(request):
	return _form(request)


@login_required
@allowed_users(allowed_roles=ROLE_POLICY_KRIA)
def PublikasaunUpdate(request, pk):
	objects = get_object_or_404(Publikasaun, pk=pk)
	if objects.status == Publikasaun.PUBLIKADU and c_user_group(request.user) not in ROLE_POLICY_PUBLIKA:
		messages.error(request, _('Publikasaun publikadu ona. Admin deit mak bele edita.'))
		return redirect('publikasaun-list')
	return _form(request, objects)


def _form(request, instance=None):
	group = request.user.groups.all()[0].name
	if request.method == 'POST':
		form = PublikasaunForm(request.POST, request.FILES, instance=instance)
		if form.is_valid():
			obj = form.save(commit=False)
			if instance is None:
				obj.created_by = request.user
			if 'file' in request.FILES:
				obj.tamanu = request.FILES['file'].size
			obj.save()
			messages.success(request, _('Publikasaun rai ona.'))
			return redirect('publikasaun-list')
	else:
		form = PublikasaunForm(instance=instance, initial={'data': timezone.localdate()})
	legend = _('Edita Publikasaun') if instance else _('Publikasaun Foun')
	context = {
		'group': group, "page": "publikasaun",
		'form': form, 'objects': instance,
		'title': legend, 'legend': legend
	}
	return render(request, 'publiku/publikasaun_form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_POLICY_PUBLIKA)
@require_POST
def PublikasaunPublika(request, pk):
	# Admin / Superadmin: publika ka subar fali husi portal
	obj = get_object_or_404(Publikasaun, pk=pk)
	if obj.status == Publikasaun.PUBLIKADU:
		obj.status, obj.published_by, obj.published_at = Publikasaun.RASCUNHO, None, None
		messages.warning(request, _('Publikasaun subar husi portal.'))
	else:
		obj.status, obj.published_by, obj.published_at = Publikasaun.PUBLIKADU, request.user, timezone.now()
		messages.success(request, _('Publikasaun mosu ona iha portal públiku.'))
	obj.save(update_fields=['status', 'published_by', 'published_at'])
	return redirect('publikasaun-list')
