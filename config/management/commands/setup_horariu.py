from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

# (naran, knaar, oras, minutu) — horáriu Timor-Leste (Asia/Dili)
HORARIU = [
	('SMKRE: autorizasaun offline', 'users.tasks.check_offline_permission', 6, 0),
	('SMKRE: lembrete prazu legál', 'legal.tasks.lembra_prazu', 7, 0),
]


class Command(BaseCommand):
	help = "Rejista knaar automátiku (Celery Beat) kada loron. Seguru atu la'o dala barak."

	def handle(self, *args, **options):
		for naran, knaar, oras, minutu in HORARIU:
			crontab, _c = CrontabSchedule.objects.get_or_create(minute=str(minutu), hour=str(oras), day_of_week='*',
				day_of_month='*', month_of_year='*', timezone=settings.TIME_ZONE)
			PeriodicTask.objects.update_or_create(name=naran, defaults={'task': knaar, 'crontab': crontab, 'enabled': True})
			self.stdout.write(self.style.SUCCESS(f'{naran}: {knaar} · {oras:02d}:{minutu:02d}'))
