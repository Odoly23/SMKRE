from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_ALL, ROLE_INPUT_KAZU, ROLE_STATUS_KAZU, ROLE_LEGAL, INVESTIGADOR
from custom.models import Munisipiu, TipuKonflitu
from kazu.forms import KazuForm, AfetaduFormSet, InsidenteFormSet, AtorFormSet, ActionForm, StatusKazuForm
from kazu.models import Kazu, KazuHistoria, STATUS_CHOICES, STATUS_KAZU_CHOICES
from kazu.permissions import kazu_queryset, can_view, can_edit
from kazu.services import available_actions, refresh_auto_fields, submit_kazu
from users.auth_utils import c_user_pesoal


@login_required
@allowed_users(allowed_roles=ROLE_ALL)
def KazuList(request):
	group = request.user.groups.all()[0].name
	objects = kazu_queryset(request.user).prefetch_related('tipu_konflitu')
	f_status = request.GET.get('status', '')
	f_mun = request.GET.get('munisipiu', '')
	f_tipu = request.GET.get('tipu', '')
	q = request.GET.get('q', '').strip()
	if f_status:
		objects = objects.filter(status=f_status)
	if f_mun:
		objects = objects.filter(munisipiu_id=f_mun)
	if f_tipu:
		objects = objects.filter(tipu_konflitu__id=f_tipu)
	if request.GET.get('urjente'):
		objects = objects.filter(urjente=True)
	if q:
		objects = objects.filter(Q(kode__icontains=q) | Q(titulu__icontains=q) | Q(suku__name__icontains=q) | Q(aldeia__name__icontains=q))
	page = Paginator(objects.distinct(), 25).get_page(request.GET.get('page'))
	context = {
		'group': group, "page": "kazu",
		'objects': page, 'status_choices': STATUS_CHOICES,
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'f_status': f_status, 'f_mun': f_mun, 'f_tipu': f_tipu, 'q': q,
		'title': _('Lista Kazu'), 'legend': _('Lista Kazu')
	}
	return render(request, 'kazu/list.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_ALL)
def KazuDetail(request, uuid):
	group = request.user.groups.all()[0].name
	objects = get_object_or_404(kazu_queryset(request.user).prefetch_related(
		'tipu_konflitu', 'estragu', 'nesesidade', 'afetadu', 'insidente__tipu_eviksaun', 'ator__tipu_ator', 'evidensia'), pk=uuid)
	context = {
		'group': group, "page": "kazu",
		'objects': objects,
		'historia': objects.historia.select_related('user__pesoaluser__pesoal')[:50],
		'actions': available_actions(request.user, objects),
		'can_edit': can_edit(request.user, objects),
		'can_status_kazu': group in ROLE_STATUS_KAZU and objects.status in ('VERIFIED', 'APPROVED', 'COMPLETED'),
		'can_legal': group in ROLE_LEGAL and objects.status in ('VERIFIED', 'APPROVED', 'COMPLETED'),
		'action_form': ActionForm(), 'status_kazu_form': StatusKazuForm(initial={'status_kazu': objects.status_kazu}),
		'status_kazu_choices': STATUS_KAZU_CHOICES,
		'title': str(objects), 'legend': _('Detalla Kazu')
	}
	return render(request, 'kazu/detail.html', context)


def _save_kazu(request, form, formsets, instance=None):
	# Rai kazu + formset hotu iha transaksaun ida; retorna kazu ka None
	with transaction.atomic():
		obj = form.save(commit=False)
		if instance is None:
			obj.created_by = request.user
		obj.save()
		form.save_m2m()
		for fs in formsets:
			fs.instance = obj
			fs.save()
		refresh_auto_fields(obj)
		KazuHistoria.objects.create(kazu=obj, user=request.user, tipu=KazuHistoria.EDITA,
			status_foun=obj.status, nota='KRIA' if instance is None else 'EDITA')
	return obj


def _form_view(request, instance=None):
	group = request.user.groups.all()[0].name
	pesoal = c_user_pesoal(request.user)
	if not pesoal or not pesoal.munisipiu:
		messages.error(request, _('Ita seidauk iha munisípiu knaar. Kontaktu Admin.'))
		return redirect('kazu-list')
	submit = request.POST.get('aksaun') == 'haruka'
	if request.method == 'POST':
		form = KazuForm(request.POST, instance=instance, munisipiu_knaar=pesoal.munisipiu, submit=submit)
		formsets = [AfetaduFormSet(request.POST, instance=instance or Kazu(), prefix='afetadu'),
			InsidenteFormSet(request.POST, instance=instance or Kazu(), prefix='insidente'),
			AtorFormSet(request.POST, instance=instance or Kazu(), prefix='ator')]
		if form.is_valid() and all(fs.is_valid() for fs in formsets):
			obj = _save_kazu(request, form, formsets, instance)
			if submit:
				try:
					obj = submit_kazu(obj, request.user)
					messages.success(request, _('Kazu %(kode)s haruka ona. Admin sei simu notifikasaun.') % {'kode': obj.kode})
				except ValidationError as e:
					messages.warning(request, _('Kazu rai ona maibé seidauk bele haruka: %(erru)s') % {'erru': ' '.join(e.messages)})
			else:
				messages.success(request, _('Kazu rai ona hanesan rascunho.'))
			return redirect('kazu-detail', uuid=obj.pk)
		messages.error(request, _('Favor hadia erru iha formuláriu.'))
	else:
		form = KazuForm(instance=instance, munisipiu_knaar=pesoal.munisipiu)
		formsets = [AfetaduFormSet(instance=instance or Kazu(), prefix='afetadu'),
			InsidenteFormSet(instance=instance or Kazu(), prefix='insidente'),
			AtorFormSet(instance=instance or Kazu(), prefix='ator')]
	legend = _('Edita Kazu') if instance else _('Rejista Kazu Foun')
	context = {
		'group': group, "page": "kazu-add" if instance is None else "kazu",
		'form': form, 'afetadu_fs': formsets[0], 'insidente_fs': formsets[1], 'ator_fs': formsets[2],
		'objects': instance,
		'title': legend, 'legend': legend
	}
	return render(request, 'kazu/form.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_INPUT_KAZU)
def KazuAdd(request):
	return _form_view(request)


@login_required
@allowed_users(allowed_roles=[INVESTIGADOR])
def KazuUpdate(request, uuid):
	objects = get_object_or_404(Kazu, pk=uuid)
	if not can_edit(request.user, objects):
		messages.error(request, _('Kazu ne\'e xave ona. Labele edita.'))
		return redirect('kazu-detail', uuid=uuid) if can_view(request.user, objects) else render(request, 'home/403.html', status=403)
	return _form_view(request, objects)
