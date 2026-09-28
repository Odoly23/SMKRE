from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Min, Q
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from config.decorators import allowed_users
from config.rbac import ROLE_LEGAL, ROLE_STATUS_KAZU
from kazu.models import Kazu, STATUS_KAZU_CHOICES
from legal.tasks import LOREN_LEMBRA
from legal.services import dokumentu_queryset, nota_queryset, can_edit_vault, KAZU_STATUS_LEGAL
from users.auth_utils import c_user_group


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL)
def LegalKazuList(request):
	# Kazu verifikadu ona: dokumentu, nota no prazu legál
	group = request.user.groups.all()[0].name
	hoje = timezone.localdate()
	objects = Kazu.objects.filter(status__in=KAZU_STATUS_LEGAL).select_related('munisipiu', 'suku').annotate(
		n_dok=Count('dokumentu_legal', filter=Q(dokumentu_legal__atual=True, dokumentu_legal__arkivadu=False), distinct=True),
		n_nota=Count('nota_legal', distinct=True),
		prazu=Min('nota_legal__prazu', filter=Q(nota_legal__remata=False, nota_legal__prazu__gte=hoje)),
	)
	status_kazu = request.GET.get('status_kazu', 'AKSAUN_LEGAL')
	if status_kazu:
		objects = objects.filter(status_kazu=status_kazu)
	q = request.GET.get('q', '').strip()
	if q:
		objects = objects.filter(Q(kode__icontains=q) | Q(titulu__icontains=q) | Q(suku__name__icontains=q))
	objects = Paginator(objects.order_by(F('prazu').asc(nulls_last=True), '-urjente', '-created_at'), 25).get_page(request.GET.get('page'))
	context = {
		'group': group, "page": "legal",
		'objects': objects, 'q': q, 'f_status_kazu': status_kazu, 'status_kazu_choices': STATUS_KAZU_CHOICES,
		'limite': hoje + timedelta(days=LOREN_LEMBRA),           # prazu besik → mean
		'title': _('Kazu Legál'), 'legend': _('Kazu iha Prosesu Legál')
	}
	return render(request, 'legal/kazu_list.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL)
def LegalKazu(request, uuid):
	group = request.user.groups.all()[0].name
	objects = get_object_or_404(Kazu.objects.select_related('munisipiu', 'postu', 'suku', 'aldeia'), pk=uuid, status__in=KAZU_STATUS_LEGAL)
	context = {
		'group': group, "page": "legal",
		'objects': objects,
		'dokumentu': dokumentu_queryset(request.user).filter(kazu=objects),
		'nota': nota_queryset(request.user, objects),
		'can_edit': can_edit_vault(request.user),
		'can_status_kazu': c_user_group(request.user) in ROLE_STATUS_KAZU,
		'status_kazu_choices': STATUS_KAZU_CHOICES,
		'hoje': timezone.localdate(),
		'title': str(objects), 'legend': _('Dossier Legál')
	}
	return render(request, 'legal/kazu_detail.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_LEGAL)
def LegalDossier(request, uuid):
	# Pájina imprime (ka "Save as PDF") ho kop Rede ba Rai — ba tribunál / autoridade
	objects = get_object_or_404(Kazu.objects.select_related('munisipiu', 'postu', 'suku', 'aldeia', 'tipu_rai'),
		pk=uuid, status__in=KAZU_STATUS_LEGAL)
	context = {
		'objects': objects,
		'dokumentu': dokumentu_queryset(request.user).filter(kazu=objects),
		'nota': nota_queryset(request.user, objects).filter(konfidensial=False),
		'historia': objects.historia.select_related('user__pesoaluser__pesoal'),
		'agora': timezone.localtime(), 'user_naran': getattr(getattr(request.user, 'pesoaluser', None), 'pesoal', request.user),
		'title': _('Dossier %(kode)s') % {'kode': objects.kode}
	}
	return render(request, 'legal/dossier.html', context)
