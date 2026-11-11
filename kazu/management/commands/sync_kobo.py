"""Tarik submission husi KoboToolbox no kria Kazu iha SIBAR-RbR.

    python manage.py sync_kobo --dry-run       # haree mapeamentu, la kria (seguru)
    python manage.py sync_kobo --amostra       # hatudu submission ida (atu hadia MAPA)
    python manage.py sync_kobo                 # kria kazu foun (hein verifikasaun)

Uza scheduled task (PythonAnywhere Tasks / cron) atu hala'o loron-loron.
"""
import json
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from config.rbac import SUPERADMIN, ADMIN


class Command(BaseCommand):
	help = 'Tarik submission husi KoboToolbox no kria Kazu'

	def add_arguments(self, p):
		p.add_argument('--dry-run', action='store_true', help='Valida de\'it, la kria kazu')
		p.add_argument('--amostra', action='store_true', help='Hatudu submission ida (JSON) atu hadia MAPA')
		p.add_argument('--limite', type=int, default=None, help='Prosesa submission to\'o N de\'it')
		p.add_argument('--user', default=None, help='Email utilizador importador (default: Admin/Superadmin dahuluk)')

	def handle(self, *a, **o):
		from kazu import kobo
		if o['amostra']:
			subs = kobo.buka_submissions(limite=1)
			if not subs:
				self.stdout.write('La iha submission iha Kobo.')
				return
			self.stdout.write(json.dumps(subs[0], indent=2, ensure_ascii=False))
			self.stdout.write(self.style.WARNING('\nHadia MAPA iha kazu/kobo.py tuir naran pergunta iha leten.'))
			return

		if o['user']:
			user = User.objects.filter(email=o['user'], is_active=True).first()
			if not user:
				raise CommandError(f'Utilizador {o["user"]} la hetan.')
		else:
			user = User.objects.filter(groups__name__in=[SUPERADMIN, ADMIN], is_active=True).order_by('pk').first()
			if not user:
				raise CommandError('La iha Admin/Superadmin. Uza --user.')

		try:
			r = kobo.sync(user, dry_run=o['dry_run'], limite=o['limite'])
		except RuntimeError as e:
			raise CommandError(str(e))
		modu = 'DRY-RUN (la kria)' if o['dry_run'] else 'KRIA'
		self.stdout.write(f'[{modu}] Kobo: total {r["total"]}, foun {r["foun"]}, kria {r["kria"]}, sala {r["sala"]}')
		for e in r['erru'][:10]:
			self.stdout.write(self.style.ERROR(f'  {e["uuid"]}: {", ".join(str(x) for x in e["erru"])}'))
		if o['dry_run'] and r.get('amostra'):
			self.stdout.write('\nAmostra:')
			for s in r['amostra']:
				self.stdout.write(f'  {"OK" if s["ok"] else "SALA"} {s["uuid"]} {s.get("rezumu") or s["erru"]}')
