from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy as _l
from config.decorators import allowed_users
from config.rbac import ROLE_PORTAL, ROLE_ALL, ROLE_DASHBOARD, ROLE_IMPORT_KAZU, ROLE_SEGIMENTU, ROLE_INPUT_KAZU, ROLE_STATUS_KAZU, ROLE_LEGAL, ROLE_DUPLIKADU, INVESTIGADOR
from custom.models import Munisipiu, TipuKonflitu
from kazu.forms import KazuForm, AfetaduFormSet, InsidenteFormSet, ActionForm, AkompanamentuForm, SegimentuKazuForm
from kazu.models import Kazu, KazuHistoria, STATUS_CHOICES, CANCELED, KazuAkompanamentu, SEKSAUN_REL
from kazu.permissions import kazu_queryset, can_view, can_edit, can_poligon
from kazu.duplikadu import posivel_duplikadu
from kazu.importa import pode_muda_lokasaun
from kazu.services import action_buttons, refresh_auto_fields, submit_kazu, enxe_fokal, can_followup, investigador_followup
from users.auth_utils import c_user_pesoal


@login_required
@allowed_users(allowed_roles=ROLE_ALL)
def KazuList(request):
	group = request.user.groups.all()[0].name
	objects = kazu_queryset(request.user).select_related('segimentu').prefetch_related('tipu_konflitu')
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
		objects = objects.filter(Q(kode__icontains=q) | Q(kode_hp__icontains=q) | Q(titulu__icontains=q) | Q(suku__name__icontains=q) | Q(aldeia__name__icontains=q))
	page = Paginator(objects.distinct(), 25).get_page(request.GET.get('page'))
	context = {
		'group': group, "page": "kazu",
		'objects': page, 'status_choices': STATUS_CHOICES,
		'munisipiu_list': Munisipiu.active.all(), 'tipu_list': TipuKonflitu.active.all(),
		'f_status': f_status, 'f_mun': f_mun, 'f_tipu': f_tipu, 'q': q,
		'title': _('Lista Kazu'), 'legend': _('Lista Kazu')
	}
	return render(request, 'kazu/list.html', context)


def desizaun_ctx():
	# Opsaun no esplikasaun Desizaun RbR (detalla kazu + detalla legál)
	from kazu.models import DESIZAUN_RBR_CHOICES, DESIZAUN_AJUDA
	return {'desizaun_choices': DESIZAUN_RBR_CHOICES,
		'desizaun_ajuda': [(c, l, DESIZAUN_AJUDA.get(c, '')) for c, l in DESIZAUN_RBR_CHOICES]}


# Aparénsia butaun aksaun + testu modal (regra ativu/xave iha kazu.services.ACTIONS)
BUTAUN_STILU = {
	'verifika': {'label': _l('Verifika'), 'css': 'btn-verified', 'icon': 'fa-check',
		'titulu': _l('Verifika kazu?'), 'mensajen': _l("Dadus sei ba Superadmin atu aprova.")},
	'aprova':   {'label': _l('Aprova'), 'css': 'btn-success', 'icon': 'fa-check-circle',
		'titulu': _l('Aprova kazu?'), 'mensajen': _l("Kazu sei mosu iha dashboard no portal públiku (dadus agregadu).")},
	'remata':   {'label': _l('Remata'), 'css': 'btn-dark', 'icon': 'fa-flag-checkered',
		'titulu': _l('Remata kazu?'), 'mensajen': _l('Marka kazu ne\'e remata (kompensasaun selu ona).')},
	'rejeita':  {'label': _l('Rejeita'), 'css': 'btn-danger', 'icon': 'fa-undo',
		'titulu': _l('Rejeita kazu?'), 'mensajen': _l('Kazu fila ba Investigadór atu hadia no haruka fali.')},
	'kansela':  {'label': _l('Kansela (falsu / duplikadu)'), 'css': 'btn-outline-secondary', 'icon': 'fa-ban',
		'titulu': _l('Kansela kazu?'), 'mensajen': _l('Ida-ne\'e final: butaun hotu sei xave.')},
}


SEG_IKON = {'status': 'fa-flag', 'tribunal': 'fa-gavel', 'notifikasaun': 'fa-envelope-o', 'fokal': 'fa-user', 'org_seluk': 'fa-users'}


def seg_seksaun(kazu):
	# Butaun + modal kada seksaun segimentu (formuláriu badak: seksaun ida de'it)
	from kazu.forms import SegimentuForm, SEGIMENTU_SEKSAUN
	from kazu.models import KazuSegimentu
	seg = getattr(kazu, 'segimentu', None) if hasattr(kazu, 'segimentu') else None
	seg = seg or KazuSegimentu(kazu=kazu)
	return [{'xave': x, 'titulu': t, 'ikon': SEG_IKON.get(x, 'fa-pencil'), 'form': SegimentuForm(instance=seg, seksaun=x, prefix=x)}
		for x, t, _r in SEGIMENTU_SEKSAUN]


@login_required
@allowed_users(allowed_roles=ROLE_ALL)
def KazuDetail(request, uuid):
	group = request.user.groups.all()[0].name
	objects = get_object_or_404(kazu_queryset(request.user).select_related(*SEKSAUN_REL).prefetch_related(
		'tipu_konflitu', 'estragu', 'nesesidade', 'afetadu', 'insidente__tipu_eviksaun', 'ator__tipu_ator', 'evidensia'), pk=uuid)
	buttons = [dict(b, **BUTAUN_STILU[b['action']]) for b in action_buttons(request.user, objects)]
	context = {
		'group': group, "page": "kazu",
		'objects': objects,
		'historia': objects.historia.select_related('user__pesoaluser__pesoal')[:50],
		'action_buttons': buttons,
		'can_mapa': group in ROLE_DASHBOARD,
		'can_lokasaun': group in ROLE_IMPORT_KAZU and pode_muda_lokasaun(objects),
		'can_portal': group in ROLE_PORTAL,   # Admin: dada marka iha mapa
		'segimentu': getattr(objects, 'segimentu', None) if hasattr(objects, 'segimentu') else None,
		'akompanamentu': objects.akompanamentu.select_related('created_by')[:30],
		'can_segimentu': group in ROLE_SEGIMENTU,
		'seg_seksaun': seg_seksaun(objects) if group in ROLE_SEGIMENTU and objects.status != CANCELED else [],
		'akomp_form': AkompanamentuForm() if group in ROLE_SEGIMENTU else None,
		'can_edit': can_edit(request.user, objects),
		'can_poligon': can_poligon(request.user, objects),
		'can_status_kazu': group in ROLE_STATUS_KAZU and objects.status in ('VERIFIED', 'APPROVED', 'COMPLETED', 'FOLLOWUP'),
		'can_legal': group in ROLE_LEGAL and objects.status in ('VERIFIED', 'APPROVED', 'COMPLETED', 'FOLLOWUP'),
		'can_followup': can_followup(request.user, objects),
		'investigador_followup': investigador_followup(objects) if can_followup(request.user, objects) else [],
		'action_form': ActionForm(),
		'duplikadu': _duplikadu(request.user, objects),
		'can_duplikadu': group in ROLE_DUPLIKADU,
		**desizaun_ctx(),
		'title': str(objects), 'legend': _('Detalla Kazu')
	}
	return render(request, 'kazu/detail.html', context)


def _duplikadu(user, kazu):
	# Avizu "posivel duplikadu" (kazu seluk GPS besik ka aldeia + tipu konflitu hanesan)
	if kazu.status == CANCELED:
		return []
	lista = posivel_duplikadu(kazu)
	for d in lista:
		d['pode_haree'] = can_view(user, d['kazu'])
	return lista


def _save_kazu(request, form, formsets, instance=None, seg_form=None):
	# Rai kazu + formset + segimentu (tribunál, notifikasaun, status) iha transaksaun ida
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
		if instance is None:
			enxe_fokal(obj, request.user)
		if seg_form is not None:                        # segimentu (fokal point automátiku la muda)
			from kazu.models import KazuSegimentu
			seg, _c = KazuSegimentu.objects.get_or_create(kazu=obj)
			for campo, valor in seg_form.cleaned_data.items():
				setattr(seg, campo, valor)
			seg.updated_by = request.user
			seg.save()
		asaun = form.cleaned_data.get('akompanamentu_foun', '').strip()
		if asaun:
			KazuAkompanamentu.objects.create(kazu=obj, data=timezone.localdate(), asaun=asaun, created_by=request.user)
		KazuHistoria.objects.create(kazu=obj, user=request.user, tipu=KazuHistoria.EDITA,
			status_foun=obj.status, nota='KRIA' if instance is None else 'EDITA')
	return obj


def _segimentu(kazu):
	from kazu.models import KazuSegimentu
	if kazu is None:
		return KazuSegimentu()
	return KazuSegimentu.objects.filter(kazu=kazu).first() or KazuSegimentu(kazu=kazu)


def _form_view(request, instance=None):
	group = request.user.groups.all()[0].name
	pesoal = c_user_pesoal(request.user)
	if not pesoal or not pesoal.munisipiu:
		messages.error(request, _('Ita seidauk iha munisípiu knaar. Kontaktu Admin.'))
		return redirect('kazu-list')
	submit = request.POST.get('aksaun') == 'haruka'
	if request.method == 'POST':
		form = KazuForm(request.POST, instance=instance, munisipiu_knaar=pesoal.munisipiu_lista, submit=submit)
		seg_form = SegimentuKazuForm(request.POST, instance=_segimentu(instance), prefix='seg')
		formsets = [AfetaduFormSet(request.POST, instance=instance or Kazu(), prefix='afetadu'),
			InsidenteFormSet(request.POST, instance=instance or Kazu(), prefix='insidente')]
		if form.is_valid() and seg_form.is_valid() and all(fs.is_valid() for fs in formsets):
			obj = _save_kazu(request, form, formsets, instance, seg_form)
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
		form = KazuForm(instance=instance, munisipiu_knaar=pesoal.munisipiu_lista)
		seg_form = SegimentuKazuForm(instance=_segimentu(instance), prefix='seg')
		formsets = [AfetaduFormSet(instance=instance or Kazu(), prefix='afetadu'),
			InsidenteFormSet(instance=instance or Kazu(), prefix='insidente')]
	legend = _('Edita Kazu') if instance else _('Rejista Kazu Foun')
	context = {
		'group': group, "page": "kazu-add" if instance is None else "kazu",
		'form': form, 'seg_form': seg_form, 'afetadu_fs': formsets[0], 'insidente_fs': formsets[1],
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
