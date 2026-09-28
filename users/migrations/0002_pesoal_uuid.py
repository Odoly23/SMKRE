import uuid
from django.db import migrations, models


def gen_uuid(apps, schema_editor):
	Pesoal = apps.get_model('users', 'Pesoal')
	for row in Pesoal.objects.all():
		row.uuid = uuid.uuid4()
		row.save(update_fields=['uuid'])


class Migration(migrations.Migration):
	dependencies = [('users', '0001_initial')]

	operations = [
		migrations.AddField(model_name='pesoal', name='uuid', field=models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
		migrations.RunPython(gen_uuid, migrations.RunPython.noop),
		migrations.AlterField(model_name='pesoal', name='uuid', field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
	]
