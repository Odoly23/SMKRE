from django.db import migrations


def hamoos(apps, schema_editor):
	# Evidénsia sein file (bug sinkron vídeo iha versaun a646e19) — la iha buat ida atu hatudu
	Evidensia = apps.get_model('kazu', 'Evidensia')
	Evidensia.objects.filter(file='').delete()


class Migration(migrations.Migration):
	dependencies = [('kazu', '0002_kazu_import')]
	operations = [migrations.RunPython(hamoos, migrations.RunPython.noop)]
