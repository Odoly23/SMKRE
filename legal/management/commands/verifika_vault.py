import hashlib
from django.core.management.base import BaseCommand
from legal.models import DokumentuLegal


class Command(BaseCommand):
	help = "Auditoria: kalkula fali SHA-256 file vault hotu no kompara ho valór rai iha base dadus."

	def handle(self, *args, **options):
		ok = erru = 0
		for doc in DokumentuLegal.objects.all().iterator():
			try:
				h = hashlib.sha256()
				with doc.file.open('rb') as f:
					for pedasu in iter(lambda: f.read(65536), b''):
						h.update(pedasu)
				if h.hexdigest() == doc.sha256:
					ok += 1
				else:
					erru += 1
					self.stdout.write(self.style.ERROR(f'MUDA: {doc.pk} "{doc.titulu}" v{doc.versaun}'))
			except (FileNotFoundError, ValueError):
				erru += 1
				self.stdout.write(self.style.ERROR(f'LA IHA FILE: {doc.pk} "{doc.titulu}" v{doc.versaun}'))
		estilu = self.style.SUCCESS if not erru else self.style.ERROR
		self.stdout.write(estilu(f'Vault: {ok} loos · {erru} problema'))
		if erru:
			raise SystemExit(1)
