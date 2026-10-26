"""Ativa input legál: Admin / Superadmin hili Ofisiál Legál ne'ebé bele input survei (online + app offline) ho data hahú–remata."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_LEGAL_AUTORIZA, OFISIAL_LEGAL
from legal.forms import AutorizasaunLegalForm
from users.auth_utils import c_user_pesoal
from users.emails import kirim_email_offline
from users.models import OfflinePermission
from users.pin import pin_se_laiha
from users.services import give_offline, cancel_offline


def _perm_legal():
	return OfflinePermission.objects.filter(user__groups__name=OFISIAL_LEGAL)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_AUTORIZA)
def AutorizasaunLegal(request):
	form = AutorizasaunLegalForm(request.POST or None, initial={'users': request.GET.getlist('user')})
	if request.method == 'POST' and form.is_valid():
		d = form.cleaned_data
		for u in d['users']:
			perm = give_offline(u, by=request.user, note=d.get('note', ''), hahu=d.get('data_hahu'), remata=d.get('data_remata'))
			kirim_email_offline(u, c_user_pesoal(u), perm, pin=pin_se_laiha(u))     # PIN app offline (se seidauk iha)
		messages.success(request, _('Input legál ativu ba Ofisiál Legál %(n)s to\'o %(date)s.') % {
			'n': len(d['users']), 'date': perm.end_date.strftime('%d/%m/%Y')})
		return redirect('legal-autorizasaun')
	from django.contrib.auth.models import User
	context = {
		"page": "legal-autoriza", 'form': form,
		'n_legal': form.fields['users'].queryset.count(),
		'n_legal_la_ativu': User.objects.filter(groups__name=OFISIAL_LEGAL, is_active=False).count(),
		'objects': _perm_legal().select_related('user__pesoaluser__pesoal', 'given_by__pesoaluser__pesoal')[:200],
		'title': _('Ativa Input Legál'), 'legend': _('Ativa Input Legál')
	}
	return render(request, 'legal/autorizasaun.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_AUTORIZA)
@require_POST
def AutorizasaunRenova(request, pk):
	obj = get_object_or_404(_perm_legal(), pk=pk, user__is_active=True)
	perm = give_offline(obj.user, by=request.user, note=_('Renova'))
	kirim_email_offline(obj.user, c_user_pesoal(obj.user), perm, pin=pin_se_laiha(obj.user))
	messages.success(request, _('Autorizasaun renova ona to\'o %(date)s.') % {'date': perm.end_date.strftime('%d/%m/%Y')})
	return redirect('legal-autorizasaun')


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL_AUTORIZA)
@require_POST
def AutorizasaunKansela(request, pk):
	obj = get_object_or_404(_perm_legal(), pk=pk)
	cancel_offline(obj.user, by=request.user, note='kansela input legál')
	messages.warning(request, _('Input legál kansela ona.'))
	return redirect('legal-autorizasaun')
