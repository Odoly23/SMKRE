import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_USER_MANAGE, SUPERADMIN
from users.auth_utils import c_user_group, c_user_offline
from users.emails import kirim_email_konta_foun, kirim_email_reset_admin
from users.forms import PesoalForm
from users.models import Pesoal, PesoalUser
from users.services import cancel_offline, revoke_tokens

logger = logging.getLogger('smkre.seguransa')


def _can_edit(request, objects):
	# Admin labele edita Superadmin; Superadmin bele edita ema hotu
	target = objects.pesoaluser.user if hasattr(objects, 'pesoaluser') else None
	if target and c_user_group(target) == SUPERADMIN and c_user_group(request.user) != SUPERADMIN:
		return False
	return True


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
def PesoalList(request):
	group = request.user.groups.all()[0].name
	objects = Pesoal.objects.select_related('pesoaluser__user', 'munisipiu', 'pos').prefetch_related('pesoaluser__user__groups')
	context = {
		'group': group, "page": "user",
		'objects': objects, 'title': _('Lista Utilizador'), 'legend': _('Lista Utilizador')
	}
	return render(request, 'users/list.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
def PesoalDetail(request, pk):
	group = request.user.groups.all()[0].name
	objects = get_object_or_404(Pesoal.objects.select_related('pesoaluser__user', 'munisipiu', 'pos'), pk=pk)
	user = objects.pesoaluser.user
	context = {
		'group': group, "page": "user",
		'objects': objects, 'u_group': c_user_group(user), 'offline': c_user_offline(user),
		'can_edit': _can_edit(request, objects),
		'title': _('Detalla Utilizador'), 'legend': _('Detalla Utilizador')
	}
	return render(request, 'users/detail.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
def PesoalAdd(request):
	group = request.user.groups.all()[0].name
	if request.method == 'POST':
		form = PesoalForm(request.POST, request.FILES, admin_group=group)
		if form.is_valid():
			with transaction.atomic():
				instance = form.save()
				password = make_password(settings.DEFAULT_PASSWORD)
				obj = User(username=instance.email, email=instance.email, password=password,
					first_name=(instance.name or '')[:150])
				obj.save()
				obj2 = PesoalUser(pesoal=instance, user=obj, must_change_password=True)
				obj2.save()
				u_group, _c = Group.objects.get_or_create(name=form.cleaned_data['role'])
				obj.groups.add(u_group)
			transaction.on_commit(lambda: kirim_email_konta_foun(obj, instance))
			logger.info(f'Utilizador foun: {obj.username} ({u_group.name}) husi {request.user.username}')
			messages.success(request, _('Utilizador foun aumenta ona. Email haruka ona ba %(email)s.') % {'email': instance.email})
			return redirect('pesoal-detail', pk=instance.pk)
	else:
		form = PesoalForm(admin_group=group)
	context = {
		'group': group, "page": "user",
		'form': form,
		'title': _('Aumenta Utilizador'), 'legend': _('Aumenta Utilizador')
	}
	return render(request, 'users/form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
def PesoalUpdate(request, pk):
	group = request.user.groups.all()[0].name
	objects = get_object_or_404(Pesoal, pk=pk)
	if not _can_edit(request, objects):
		return render(request, 'home/403.html', status=403)
	user = objects.pesoaluser.user
	if request.method == 'POST':
		form = PesoalForm(request.POST, request.FILES, instance=objects, admin_group=group)
		if form.is_valid():
			with transaction.atomic():
				instance = form.save()
				user.username = instance.email
				user.email = instance.email
				user.first_name = (instance.name or '')[:150]
				user.save()
				user.groups.set([Group.objects.get_or_create(name=form.cleaned_data['role'])[0]])
			messages.success(request, _('Dadus utilizador atualiza ona.'))
			return redirect('pesoal-detail', pk=instance.pk)
	else:
		form = PesoalForm(instance=objects, admin_group=group, initial_role=c_user_group(user))
	context = {
		'group': group, "page": "user",
		'form': form, 'objects': objects,
		'title': _('Edita Utilizador'), 'legend': _('Edita Utilizador')
	}
	return render(request, 'users/form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
@require_POST
def UserResetPassword(request, pk):
	objects = get_object_or_404(Pesoal, pk=pk)
	if not _can_edit(request, objects):
		return render(request, 'home/403.html', status=403)
	user = objects.pesoaluser.user
	user.password = make_password(settings.DEFAULT_PASSWORD)
	user.save(update_fields=['password'])
	PesoalUser.objects.filter(pk=objects.pesoaluser.pk).update(must_change_password=True)
	revoke_tokens(user)
	kirim_email_reset_admin(user, objects)
	logger.info(f'Reset password: {user.username} husi {request.user.username}')
	messages.success(request, _('Password %(user)s reset ona no haruka ona ba email.') % {'user': user.username})
	return redirect('pesoal-detail', pk=pk)


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
@require_POST
def UserActivate(request, pk):
	objects = get_object_or_404(Pesoal, pk=pk)
	user = objects.pesoaluser.user
	if not _can_edit(request, objects) or user == request.user:
		return render(request, 'home/403.html', status=403)
	user.is_active = not user.is_active
	user.save(update_fields=['is_active'])
	if not user.is_active:
		cancel_offline(user, by=request.user, note='utilizador hapara')
		messages.warning(request, _('Utilizador %(user)s hapara ona. Autorizasaun offline no token kansela.') % {'user': user.username})
	else:
		messages.success(request, _('Utilizador %(user)s ativu fali.') % {'user': user.username})
	logger.info(f'Utilizador {"ativu" if user.is_active else "hapara"}: {user.username} husi {request.user.username}')
	return redirect('pesoal-detail', pk=pk)
