from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_ALL, ROLE_INPUT_KAZU, ROLE_STATUS_KAZU, ROLE_FOLLOWUP, ROLE_PORTAL, ROLE_DUPLIKADU
from kazu.models import Kazu
from kazu.permissions import can_view, is_responsavel
from kazu.services import muda_portal, submit_kazu, change_status, muda_desizaun, followup_kazu, marka_la_os_duplikadu, STATUS_LABEL


@login_required
@allowed_users(allowed_roles=ROLE_INPUT_KAZU)
@require_POST
def KazuSubmit(request, uuid):
	# Investigadór haruka kazu ba Admin (online)
	objects = get_object_or_404(Kazu, pk=uuid)
	if not is_responsavel(request.user, objects):
		return render(request, 'home/403.html', status=403)
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
		muda_desizaun(objects, request.user, request.POST.get('desizaun_rbr'), request.POST.get('nota', ''))
		messages.success(request, _('Desizaun RbR atualiza ona.'))
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	# Fila ba pájina orijen (ex. pájina Legál) se link seguru
	next_url = request.POST.get('next', '')
	if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
		return redirect(next_url)
	return redirect('kazu-detail', uuid=uuid)


@login_required
@allowed_users(allowed_roles=ROLE_FOLLOWUP)
@require_POST
def KazuFollowup(request, uuid):
	# Follow-up: kazu loke fali ba Investigadór (hili) atu tuun ba terrenu → haruka fali → Verifika → Aprova
	from django.contrib.auth.models import User
	objects = get_object_or_404(Kazu, pk=uuid)
	investigador = User.objects.filter(pk=request.POST.get('investigador') or 0).first()
	try:
		objects = followup_kazu(objects, request.user, investigador, request.POST.get('nota', ''))
		messages.success(request, _('Follow-up haruka ona. Investigadór sei simu notifikasaun.'))
	except PermissionDenied:
		return render(request, 'home/403.html', status=403)
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	return redirect('kazu-detail', uuid=uuid)


@login_required
@allowed_users(allowed_roles=ROLE_PORTAL)
@require_POST
def KazuPortal(request, uuid):
	# Admin / Superadmin: konsentimentu + hatudu kazu iha portal públiku
	objects = get_object_or_404(Kazu, pk=uuid)
	if not can_view(request.user, objects):
		return render(request, 'home/403.html', status=403)
	konsentimentu, publika = request.POST.get('konsentimentu') == '1', request.POST.get('publika') == '1'
	if publika and not konsentimentu:
		messages.warning(request, _('Kazu labele hatudu iha portal se laiha konsentimentu.'))
	if muda_portal(objects, request.user, konsentimentu, publika):
		messages.success(request, _('Portal públiku: rai ona.') + ('' if objects.iha_portal or not (publika and konsentimentu) else ' ' + _('Kazu sei mosu hafoin Superadmin aprova.')))
	return redirect('kazu-detail', uuid=uuid)


@login_required
@allowed_users(allowed_roles=ROLE_DUPLIKADU)
@require_POST
def KazuLaOsDuplikadu(request, uuid, outro):
	# Admin / Superadmin: kazu rua la'ós hanesan → hasai avizu duplikadu
	objects = get_object_or_404(Kazu, pk=uuid)
	outro_obj = get_object_or_404(Kazu, pk=outro)
	try:
		marka_la_os_duplikadu(objects, request.user, outro_obj)
		messages.success(request, _("Marka ona: %(a)s la'ós duplikadu ho %(b)s.") % {'a': objects, 'b': outro_obj})
	except PermissionDenied:
		return render(request, 'home/403.html', status=403)
	except ValidationError as e:
		messages.error(request, ' '.join(e.messages))
	return redirect('kazu-detail', uuid=uuid)
