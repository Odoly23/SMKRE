from django.db import migrations, models


def enxe_tinan(apps, schema_editor):
	Kazu = apps.get_model('kazu', 'Kazu')
	for k in Kazu.objects.exclude(data_relatoriu=None).only('pk', 'data_relatoriu'):
		Kazu.objects.filter(pk=k.pk).update(tinan_simu=k.data_relatoriu.year)


class Migration(migrations.Migration):
	dependencies = [('kazu', '0011_referensia_rbr')]
	operations = [
		migrations.AddField(model_name='kazu', name='tinan_simu', field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Tinan Simu Kazu iha RbR')),
		migrations.RunPython(enxe_tinan, migrations.RunPython.noop),
	]
