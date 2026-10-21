"""Cek rápidu modulu Legál iha server: migrasaun, utilizador Ofisiál Legál, autorizasaun input.
Uza: python manage.py cek_legal"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from django.urls import reverse, NoReverseMatch
from config.rbac import OFISIAL_LEGAL, ADMIN, SUPERADMIN


class Command(BaseCommand):
	help = "Cek modulu Legál (migrasaun, Ofisiál Legál, autorizasaun input)"

	def handle(self, *args, **opts):
		ok = self.style.SUCCESS('OK')
		erru = lambda m: self.style.ERROR(m)
		ex = MigrationExecutor(connection)
		pendente = ex.migration_plan(ex.loader.graph.leaf_nodes())
		self.stdout.write(f'Migrasaun: {ok if not pendente else erru(f"{len(pendente)} seidauk aplika → python manage.py migrate")}')
		try:
			self.stdout.write(f'URL Ativa Input Legál: {reverse("legal-autorizasaun")} {ok}')
		except NoReverseMatch:
			self.stdout.write(erru('URL Ativa Input Legál la iha → git pull + Reload'))
		from users.models import OfflinePermission
		legal = User.objects.filter(groups__name=OFISIAL_LEGAL)
		self.stdout.write(f'Ofisiál Legál: {legal.filter(is_active=True).count()} ativu, {legal.filter(is_active=False).count()} la ativu')
		for u in legal:
			p = OfflinePermission.objects.valid().filter(user=u).first()
			self.stdout.write(f'  - {u.username}: konta {"ativu" if u.is_active else "LA ATIVU"} · input legál ' +
				(f'ATIVU to\'o {p.end_date:%d/%m/%Y}' if p else 'la ativu'))
		adm = User.objects.filter(groups__name__in=[ADMIN, SUPERADMIN], is_active=True).count()
		self.stdout.write(f'Admin / Superadmin ne\'ebé bele ativa: {adm}')
		if not legal.exists():
			self.stdout.write(erru('La iha utilizador ho papél Ofisiál Legál → kria iha menu Utilizador (papél "Ofisiál Legál").'))
