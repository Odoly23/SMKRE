from django.core.management.base import BaseCommand
from legal.tasks import lembra_prazu
from users.tasks import check_offline_permission


class Command(BaseCommand):
	help = ("Halo knaar kada loron (la presiza Celery / Redis): hamate autorizasaun offline remata + lembrete, "
		"no lembrete prazu legál. Uza iha hosting sein Celery Beat (ex. PythonAnywhere → Tasks).")

	def handle(self, *args, **options):
		self.stdout.write(f'Autorizasaun offline: {check_offline_permission()}')
		self.stdout.write(f'Prazu legál: {lembra_prazu()}')
