from django.core.management.base import BaseCommand
from legal.tasks import lembra_prazu
from users.tasks import check_offline_permission
from kazu.tasks import limpeza_automatiku


class Command(BaseCommand):
	help = ("Halo knaar kada loron (la presiza Celery / Redis): hamate autorizasaun offline remata + lembrete, "
		"lembrete prazu legál no limpeza kazu loron 30. Uza iha hosting sein Celery Beat (ex. cPanel → Cron Jobs).")

	# halo knaar loron (hosting sein Celery): autorizasaun offline, lembrete prazu legál, limpeza kazu loron 30
	def handle(self, *args, **options):
		self.stdout.write(f'Autorizasaun offline: {check_offline_permission()}')
		self.stdout.write(f'Prazu legál: {lembra_prazu()}')
		self.stdout.write(f'Limpeza kazu: {limpeza_automatiku()}')
