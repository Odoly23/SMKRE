from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import INVESTIGADOR
from config.upload_utils import compress_image
from kazu.forms import EvidensiaForm
from kazu.models import Kazu, Evidensia
from kazu.permissions import can_edit
from kazu.services import refresh_auto_fields


@login_required
@allowed_users(allowed_roles=[INVESTIGADOR])
def EvidensiaAdd(request, uuid):
	group = request.user.groups.all()[0].name
	kazu = get_object_or_404(Kazu, pk=uuid)
	if not can_edit(request.user, kazu):
		return render(request, 'home/403.html', status=403)
	if request.method == 'POST':
		form = EvidensiaForm(request.POST, request.FILES, kazu=kazu)
		if form.is_valid():
			# File ida ka barak (galeria): kada file = evidénsia ida
			for f in form.cleaned_data['file']:
				instance = Evidensia(kazu=kazu, uploaded_by=request.user, tipu=form.cleaned_data['tipu'], file=f,
					naran=form.cleaned_data.get('naran', ''), deskrisaun=form.cleaned_data.get('deskrisaun', ''),
					latitude=kazu.latitude, longitude=kazu.longitude)
				if instance.tipu == Evidensia.FOTO:
					small = compress_image(f)
					if small:
						instance.file = small
				instance.save()
			refresh_auto_fields(kazu)
			messages.success(request, _('Evidénsia aumenta ona.'))
			return redirect('kazu-evidensia', uuid=uuid)
	else:
		form = EvidensiaForm(kazu=kazu)
	context = {
		'group': group, "page": "kazu",
		'form': form, 'kazu': kazu, 'objects': kazu.evidensia.all(),
		'title': _('Evidénsia'), 'legend': _('Evidénsia Kazu')
	}
	return render(request, 'kazu/evidensia_form.html', context)


@login_required
@allowed_users(allowed_roles=[INVESTIGADOR])
@require_POST
def EvidensiaDelete(request, uuid, pk):
	kazu = get_object_or_404(Kazu, pk=uuid)
	if not can_edit(request.user, kazu):
		return render(request, 'home/403.html', status=403)
	get_object_or_404(Evidensia, pk=pk, kazu=kazu).delete()
	messages.warning(request, _('Evidénsia hamoos ona.'))
	return redirect('kazu-evidensia', uuid=uuid)
