from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver


# logout → sesaun ativu hamoos (dispozitivu seluk bele login kedas)
@receiver(user_logged_out)
def hamoos_sesaun_ativu(sender, request, user, **kwargs):
	if user is not None and request is not None and getattr(request, 'session', None) is not None:
		from users.models import SesaunAtivu
		SesaunAtivu.objects.filter(user=user, session_key=request.session.session_key).delete()
