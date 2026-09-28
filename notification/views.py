from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from notification.models import Notification
from users.auth_utils import c_user_group


@login_required
def NotificationList(request):
	group = c_user_group(request.user)
	objects = Notification.objects.filter(recipient=request.user)[:200]
	context = {
		'group': group, "page": "notif",
		'objects': objects, 'title': _('Notifikasaun'), 'legend': _('Notifikasaun'),
	}
	return render(request, 'notification/list.html', context)


@login_required
def NotificationOpen(request, pk):
	# Klik notifikasaun → marka lee ona → ba link kazu
	obj = get_object_or_404(Notification, pk=pk, recipient=request.user)
	if not obj.is_read:
		obj.is_read = True
		obj.read_at = timezone.now()
		obj.save(update_fields=['is_read', 'read_at'])
	if obj.url and url_has_allowed_host_and_scheme(obj.url, allowed_hosts={request.get_host()}):
		return redirect(obj.url)
	return redirect('notification-list')


@login_required
@require_POST
def NotificationReadAll(request):
	Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
	return redirect('notification-list')
