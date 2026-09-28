import csv
from pathlib import Path
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from config.rbac import ROLE_ALL
from custom.data import opsaun
from custom.models import Munisipiu, PostuAdministrativu, Pozisaun, TipuKonflitu, TipuRai, \
	TipuEviksaun, TipuAtor, EstraguPatrimoniu, NesesidadeUrjente

DATA_DIR = Path(__file__).resolve().parents[2] / 'data'


class Command(BaseCommand):
	help = "Prepara SMKRE: kria role (Group), opsaun padronizadu no Munisípiu + Postu. Seguru atu la'o dala barak."

	@transaction.atomic
	def handle(self, *args, **options):
		# 1. Role (RBAC)
		for role in ROLE_ALL:
			Group.objects.get_or_create(name=role)
		self.stdout.write(self.style.SUCCESS(f'Role: {", ".join(ROLE_ALL)}'))

		# 2. Opsaun padronizadu
		lista = [
			(Pozisaun, opsaun.POZISAUN), (TipuKonflitu, opsaun.TIPU_KONFLITU), (TipuRai, opsaun.TIPU_RAI),
			(TipuEviksaun, opsaun.TIPU_EVIKSAUN), (TipuAtor, opsaun.TIPU_ATOR),
			(EstraguPatrimoniu, opsaun.ESTRAGU_PATRIMONIU), (NesesidadeUrjente, opsaun.NESESIDADE_URJENTE),
		]
		for model, items in lista:
			for i, item in enumerate(items, start=1):
				defaults = {'name': item[1], 'order': i}
				if len(item) > 2:
					defaults['presiza_esplika'] = item[2]
				model.objects.update_or_create(code=item[0], defaults=defaults)
			self.stdout.write(f'  {model._meta.verbose_name}: {len(items)}')

		# 3. Munisípiu no Postu Administrativu
		with open(DATA_DIR / 'munisipiu.csv', encoding='utf-8') as f:
			for i, row in enumerate(csv.DictReader(f), start=1):
				Munisipiu.objects.update_or_create(code=row['code'], defaults={
					'name': row['name'], 'order': i,
					'latitude': row['latitude'] or None, 'longitude': row['longitude'] or None})
		with open(DATA_DIR / 'postu.csv', encoding='utf-8') as f:
			for i, row in enumerate(csv.DictReader(f), start=1):
				mun = Munisipiu.objects.get(code=row['munisipiu'])
				PostuAdministrativu.objects.update_or_create(code=row['code'], defaults={
					'name': row['name'], 'munisipiu': mun, 'order': i})
		self.stdout.write(self.style.SUCCESS(
			f'Munisípiu: {Munisipiu.objects.count()} · Postu: {PostuAdministrativu.objects.count()}'))
		self.stdout.write('Suku no Aldeia: uza "python manage.py import_wilayah <file.csv>"')
