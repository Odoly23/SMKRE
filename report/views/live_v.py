"""Ekran Live (desktop all-in-one): ekran tomak, atualiza automátiku, ekran la toba.
- Staf ho login: /report/live/
- Ekran kiosk: /live/<token>/ (link privadu husi Admin, la presiza login; dadus agregadu no anónimu de'it)"""
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from config.decorators import allowed_users
from config.rbac import ROLE_DASHBOARD, ROLE_USER_MANAGE
from report.live import dadus, CACHE_SEG
from report.models import LiveEkran

ATUALIZA_SEG = 30


def _resposta(d):
	r = JsonResponse(d)
	r['Cache-Control'] = 'private, no-store'
	return r


def _pajina(request, data_url, naran):
	r = render(request, 'report/live.html', {'data_url': data_url, 'naran_ekran': naran, 'atualiza_seg': ATUALIZA_SEG})
	r['Referrer-Policy'] = 'no-referrer'             # token iha URL la sai ba fatin seluk
	r['X-Robots-Tag'] = 'noindex, nofollow'
	return r


@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
@never_cache
def LiveStaff(request):
	return _pajina(request, reverse('report-live-dadus'), '')


@login_required
@allowed_users(allowed_roles=ROLE_DASHBOARD)
def LiveStaffDadus(request):
	return _resposta(dadus())


def _ekran(token):
	ek = LiveEkran.husi_token(token)
	if not ek:
		raise Http404
	agora = timezone.now()
	if not ek.last_seen or agora - ek.last_seen > timedelta(minutes=5):
		LiveEkran.objects.filter(pk=ek.pk).update(last_seen=agora)
	return ek


@never_cache
def LiveKiosk(request, token):
	ek = _ekran(token)
	return _pajina(request, reverse('live-kiosk-dadus', args=[token]), ek.naran)


def LiveKioskDadus(request, token):
	_ekran(token)
	return _resposta(dadus())


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
def LiveEkranList(request):
	link_foun = request.session.pop('live_link_foun', None)
	context = {
		"page": "dashboard", 'objects': LiveEkran.objects.select_related('created_by__pesoaluser__pesoal'),
		'link_foun': link_foun, 'title': _('Ekran Live'), 'legend': _('Ekran Live (link privadu)'),
	}
	return render(request, 'report/live_ekran.html', context)


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
@require_POST
def LiveEkranAdd(request):
	naran = (request.POST.get('naran') or '').strip()[:100] or _('Ekran Live')
	ek, token = LiveEkran.kria(naran, request.user)
	request.session['live_link_foun'] = {'naran': ek.naran, 'url': request.build_absolute_uri(reverse('live-kiosk', args=[token]))}
	messages.success(request, _('Link ekran live kria ona. Kopia agora: link ne\'e hatudu dala ida de\'it.'))
	return redirect('report-live-ekran')


@login_required
@allowed_users(allowed_roles=ROLE_USER_MANAGE)
@require_POST
def LiveEkranKansela(request, pk):
	ek = get_object_or_404(LiveEkran, pk=pk)
	ek.ativu = False
	ek.save(update_fields=['ativu'])
	messages.warning(request, _('Link ekran "%(n)s" kansela ona. Ekran ne\'e la bele loke tan.') % {'n': ek.naran})
	return redirect('report-live-ekran')
