from django.core.management.base import BaseCommand
from kazu.limpeza import hala_o, LORON


class Command(BaseCommand):
	help = (f"Limpeza automátiku kazu: loron {LORON} la verifika / la aprova → kansela; loron {LORON} tan → hamoos. "
		"Uza --dry-run atu haree de'it (la muda buat ida).")

	# parámetru: --dry-run (pratinjau)
	def add_arguments(self, parser):
		parser.add_argument('--dry-run', action='store_true', help="Haree kazu ne'ebé sei kansela / hamoos, la muda buat ida")

	# hala'o limpeza (ka pratinjau)
	def handle(self, *args, **options):
		rez = hala_o(simula=options['dry_run'])
		if not options['dry_run']:
			self.stdout.write(self.style.SUCCESS(f'Limpeza: {rez}'))
			return
		self.stdout.write(self.style.WARNING('[DRY-RUN — la muda buat ida]'))
		for titulu, chave in (('Sei kansela ohin', 'lista_kansela'), ('Sei hamoos permanente ohin', 'lista_hamoos'),
				('Sei kansela iha loron 9 tuir mai', 'lista_tuir_mai')):
			lista = rez[chave]
			self.stdout.write(f'{titulu}: {len(lista)}')
			for item in lista:
				self.stdout.write(f'  - {item}')
