from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_SEGIMENTU
from kazu.forms import SegimentuForm, AkompanamentuForm, SEGIMENTU_SEKSAUN, SEGIMENTU_KAMPU
from kazu.models import Kazu, KazuHistoria, KazuSegimentu, CANCELED
from users.auth_utils import c_user_group


def _hatudu(obj, campo):
	# Valór ba rezumu seksaun (label opsaun, data d/m/Y)
	v = getattr(obj, campo)
	if v in (None, ''):
		return ''
	if obj._meta.get_field(campo).choices:
		return str(getattr(obj, f'get_{campo}_display')())
	if hasattr(v, 'strftime'):
		return v.strftime('%d/%m/%Y')
	return str(v)


@login_required
@allowed_users(allowed_roles=ROLE_SEGIMENTU)
def KazuSegimentuUpdate(request, uuid):
	# Segimentu kazu (eskritóriu): seksaun ida-idak iha butaun Edita rasik → rai seksaun ne'e de'it
	group = c_user_group(request.user)
	kazu = get_object_or_404(Kazu, pk=uuid)
	if kazu.status == CANCELED:
		messages.error(request, _('Kazu kanseladu — final.'))
		return redirect('kazu-detail', uuid=uuid)
	objects, _foun = KazuSegimentu.objects.get_or_create(kazu=kazu)
	loke, form_erru = None, None
	if request.method == 'POST':
		loke = request.POST.get('seksaun')
		if loke not in SEGIMENTU_KAMPU:
			return redirect('kazu-segimentu', uuid=uuid)
		form = SegimentuForm(request.POST, instance=objects, seksaun=loke, prefix=loke)
		if form.is_valid():
			instance = form.save(commit=False)
			instance.updated_by = request.user
			instance.save()
			if form.changed_data:
				KazuHistoria.objects.create(kazu=kazu, user=request.user, tipu=KazuHistoria.EDITA,
					status_foun=kazu.status, nota=_('Segimentu atualiza: %(c)s') % {'c': ', '.join(str(form.fields[c].label) for c in form.changed_data)})
			messages.success(request, _('Segimentu kazu rai ona.'))
			if request.POST.get('next') == 'detalla':
				return redirect(reverse('kazu-detail', args=[uuid]) + '#segimentu')
			return redirect(reverse('kazu-segimentu', args=[uuid]) + f'#seksaun-{loke}')
		form_erru = form
	seksaun = []
	for n, (xave, titulu, _rows) in enumerate(SEGIMENTU_SEKSAUN, start=1):
		form = form_erru if form_erru is not None and xave == loke else SegimentuForm(instance=objects, seksaun=xave, prefix=xave)
		rezumu = [(KazuSegimentu._meta.get_field(c).verbose_name, _hatudu(objects, c)) for c in SEGIMENTU_KAMPU[xave]]
		seksaun.append({'num': n, 'xave': xave, 'titulu': titulu, 'form': form, 'loke': xave == loke,
			'rezumu': rezumu, 'iha_dadus': any(v for _l, v in rezumu)})
	context = {
		'group': group, "page": "kazu",
		'seksaun': seksaun, 'kazu': kazu, 'objects': objects,
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
