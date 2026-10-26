import logging
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_OFFLINE_FO, ROLE_USER_MANAGE, ROLE_INPUT_OFFLINE, INVESTIGADOR
from users.auth_utils import c_user_pesoal
from users.emails import kirim_email_offline
from users.forms import OfflinePermissionForm
from users.models import OfflinePermission
from users.pin import kria_pin, rai_pin, pin_se_laiha, lee_pin
from users.services import give_offline, cancel_offline


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
def OfflineList(request):
	group = request.user.groups.all()[0].name
	objects = OfflinePermission.objects.filter(user__groups__name__in=ROLE_INPUT_OFFLINE).distinct().select_related('user__pesoaluser__pesoal__munisipiu', 'given_by').prefetch_related('user__groups')[:300]
	context = {
		'group': group, "page": "offline",
		'objects': objects, 'can_haree_pin': group in ROLE_USER_MANAGE,
		'title': _('Autorizasaun Offline'), 'legend': _('Autorizasaun Offline'),
	}
	return render(request, 'users/offline_list.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_OFFLINE_FO)
def OfflineGive(request):
	group = request.user.groups.all()[0].name
	if request.method == 'POST':
		form = OfflinePermissionForm(request.POST)
		if form.is_valid():
			user = form.cleaned_data['user']
			perm = give_offline(user, by=request.user, note=form.cleaned_data.get('note', ''),
				hahu=form.cleaned_data.get('data_hahu'), remata=form.cleaned_data.get('data_remata'))
			pin = form.cleaned_data.get('pin') or kria_pin()
			rai_pin(user, pin)
			kirim_email_offline(user, c_user_pesoal(user), perm, pin=pin)
			messages.success(request, _('Autorizasaun offline fó ona to\'o %(date)s. PIN app: %(pin)s (haruka ona ba %(email)s).') % {
				'date': perm.end_date.strftime('%d/%m/%Y'), 'pin': pin, 'email': user.email})
			return redirect('offline-list')
	else:
		form = OfflinePermissionForm(initial={'user': request.GET.get('user')})
	context = {
		'group': group, "page": "offline",
		'form': form,
		'title': _('Fó Autorizasaun Offline'), 'legend': _('Fó Autorizasaun Offline'),
	}
	return render(request, 'users/offline_form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_OFFLINE_FO)
@require_POST
def OfflineRenew(request, pk):
	obj = get_object_or_404(OfflinePermission, pk=pk)
	if not obj.user.is_active or not obj.user.groups.filter(name__in=ROLE_INPUT_OFFLINE).exists():
		messages.error(request, _('Utilizador ne\'e labele hetan autorizasaun offline.'))
		return redirect('offline-list')
	perm = give_offline(obj.user, by=request.user, note=_('Renova'))
	kirim_email_offline(obj.user, c_user_pesoal(obj.user), perm, pin=pin_se_laiha(obj.user))   # PIN la muda se iha ona
	messages.success(request, _('Autorizasaun renova ona to\'o %(date)s.') % {'date': perm.end_date.strftime('%d/%m/%Y')})
	return redirect('offline-list')


@login_required
@allowed_users(allowed_roles=ROLE_OFFLINE_FO)
@require_POST
def OfflineCancel(request, pk):
	obj = get_object_or_404(OfflinePermission, pk=pk)
	cancel_offline(obj.user, by=request.user, note='kansela husi Admin')
	messages.warning(request, _('Autorizasaun offline kansela ona.'))
	return redirect('offline-list')


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
@require_POST
def OfflinePin(request, pk):
	# Admin / Superadmin haree PIN app offline (utilizador haluha PIN iha terrenu → telefone Admin). Rejista iha log seguransa.
	obj = get_object_or_404(OfflinePermission.objects.select_related('user'), pk=pk)
	pin = lee_pin(obj.user)
	logging.getLogger('smkre.seguransa').warning(f'PIN offline haree: {obj.user.username} husi {request.user.username}'
		+ ('' if pin else ' (la iha PIN atu hatudu)'))
	if not pin:
		return JsonResponse({'erru': _('PIN ida-ne\'e la bele hatudu (rai antes funsaun ne\'e ka utilizador kria PIN rasik). '
			'Fó PIN foun liuhusi "Fó Autorizasaun"; utilizador tenke "Sai / troka utilizador" iha app no login fali.')})
	return JsonResponse({'pin': pin, 'naran': str(getattr(getattr(obj.user, 'pesoaluser', None), 'pesoal', None) or obj.user.username)})
