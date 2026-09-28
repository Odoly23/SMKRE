from pathlib import Path
import polib
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	help = "Compila tradusaun locale/*/LC_MESSAGES/django.po → django.mo (la presiza gettext / msgfmt)."

	def handle(self, *args, **options):
		for base in settings.LOCALE_PATHS:
			for po_path in sorted(Path(base).glob('*/LC_MESSAGES/*.po')):
				po = polib.pofile(str(po_path))
				po.save_as_mofile(str(po_path.with_suffix('.mo')))
				self.stdout.write(self.style.SUCCESS(f'{po_path.parent.parent.name}: {po.percent_translated()}% tradus ({len(po.translated_entries())} testu)'))
