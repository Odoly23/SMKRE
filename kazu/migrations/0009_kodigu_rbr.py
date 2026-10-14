import re
from django.db import migrations

KODIGU_TUAN = re.compile(r'^(?:SMKRE|SIBAR)-([A-Z]+)-(\d{4})-(\d+)$')


def troka_kodigu(apps, schema_editor):
	# SMKRE-AIL-2026-00008 / SIBAR-AIL-2026-00008 → RbR-AIL-2026-0008 (númeru hanesan, kontador la muda)
	Kazu = apps.get_model('kazu', 'Kazu')
	for kazu in Kazu.objects.exclude(kode=None).only('pk', 'kode').iterator():
		m = KODIGU_TUAN.match(kazu.kode)
		if not m:
			continue
		foun = f'RbR-{m.group(1)}-{m.group(2)}-{int(m.group(3)):04d}'
		if not Kazu.objects.filter(kode=foun).exclude(pk=kazu.pk).exists():
			Kazu.objects.filter(pk=kazu.pk).update(kode=foun)


class Migration(migrations.Migration):
	dependencies = [('kazu', '0008_fokal_otomatiku')]
	operations = [migrations.RunPython(troka_kodigu, migrations.RunPython.noop)]
