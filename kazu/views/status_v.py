from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_ALL, ROLE_INPUT_KAZU, ROLE_STATUS_KAZU
from kazu.models import Kazu
from kazu.permissions import can_view
from kazu.services import submit_kazu, change_status, change_status_kazu, STATUS_LABEL


@login_required
@allowed_users(allowed_roles=ROLE_INPUT_KAZU)
@require_POST
def KazuSubmit(request, uuid):
	# Investigadór haruka kazu ba Admin (online)
	objects = get_object_or_404(Kazu, pk=uuid, created_by=request.user)
	try:
		objects = submit_kazu(objects, request.user)
		messages.success(request, _('Kazu %(kode)s haruka ona. Admin sei simu notifikasaun.') % {'kode': objects.kode})
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	return redirect('kazu-detail', uuid=uuid)


@login_required
@allowed_users(allowed_roles=ROLE_ALL)
@require_POST
def KazuAction(request, uuid, action):
	# Butaun iha okos detalla kazu: Verifika (Admin) · Aprova (Superadmin) · Remata · Rejeita · Kansela
	objects = get_object_or_404(Kazu, pk=uuid)
	if not can_view(request.user, objects):
		return render(request, 'home/403.html', status=403)
	try:
		objects = change_status(objects, request.user, action, request.POST.get('nota', ''))
		messages.success(request, _('Status muda ona ba %(status)s.') % {'status': STATUS_LABEL[objects.status]})
	except PermissionDenied:
		return render(request, 'home/403.html', status=403)
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	return redirect('kazu-detail', uuid=uuid)


@login_required
@allowed_users(allowed_roles=ROLE_STATUS_KAZU)
@require_POST
def KazuStatusKazu(request, uuid):
	objects = get_object_or_404(Kazu, pk=uuid)
	try:
		change_status_kazu(objects, request.user, request.POST.get('status_kazu'), request.POST.get('nota', ''))
		messages.success(request, _('Status kazu atualiza ona.'))
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	# Fila ba pájina orijen (ex. pájina Legál) se link seguru
	next_url = request.POST.get('next', '')
	if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
		return redirect(next_url)
	return redirect('kazu-detail', uuid=uuid)
