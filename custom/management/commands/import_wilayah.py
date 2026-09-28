import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from custom.models import PostuAdministrativu, Suku, Aldeia


class Command(BaseCommand):
	help = ("Import Suku no Aldeia husi CSV. Kolun: postu_code,suku_code,suku,aldeia_code,aldeia[,latitude,longitude]. "
		"Aldeia bele mamuk (import suku deit). Seguru atu la'o dala barak (update_or_create).")

	def add_arguments(self, parser):
		parser.add_argument('csv_file')

	@transaction.atomic
	def handle(self, *args, **options):
		n_suku, n_aldeia, erru = 0, 0, []
		try:
			f = open(options['csv_file'], encoding='utf-8-sig')
		except OSError as e:
			raise CommandError(f'La bele loke file: {e}')
		with f:
			for line, row in enumerate(csv.DictReader(f), start=2):
				try:
					postu = PostuAdministrativu.objects.get(code=row['postu_code'].strip())
				except PostuAdministrativu.DoesNotExist:
					erru.append(f'liña {line}: postu "{row["postu_code"]}" la iha')
					continue
				suku, created = Suku.objects.update_or_create(code=row['suku_code'].strip(), defaults={
					'name': row['suku'].strip(), 'postu': postu,
					'latitude': (row.get('latitude') or '').strip() or None,
					'longitude': (row.get('longitude') or '').strip() or None})
				n_suku += int(created)
				if (row.get('aldeia_code') or '').strip():
					_, created = Aldeia.objects.update_or_create(code=row['aldeia_code'].strip(), defaults={
						'name': row['aldeia'].strip(), 'suku': suku})
					n_aldeia += int(created)
		for e in erru:
			self.stderr.write(self.style.WARNING(e))
		self.stdout.write(self.style.SUCCESS(f'Suku foun: {n_suku} · Aldeia foun: {n_aldeia} · Erru: {len(erru)}'))
