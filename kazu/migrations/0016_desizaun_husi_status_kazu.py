"""Status Kazu tuan → Desizaun RbR (segimentu) ba kazu ne'ebé seidauk iha Desizaun RbR.
Aksaun Legál → Advokasia ativu · Taka → Arkivu · Abertu / Investigasaun → Monitorizasaun.
Desizaun RbR ne'ebé iha ona (ex. husi Airtable) la muda. Status Kazu tuan rai nafatin iha DB."""
from django.db import migrations

MAPA = {'AKSAUN_LEGAL': 'ADVOKASIA', 'TAKA': 'ARKIVU', 'ABERTU': 'MONITORIZASAUN', 'INVESTIGASAUN': 'MONITORIZASAUN'}


def ba_desizaun(apps, schema_editor):
	Kazu = apps.get_model('kazu', 'Kazu')
	Seg = apps.get_model('kazu', 'KazuSegimentu')
	for kazu_id, sk in Kazu.objects.values_list('id', 'status_kazu'):
		valor = MAPA.get(sk)
		if not valor:
			continue
		seg, _c = Seg.objects.get_or_create(kazu_id=kazu_id)
		if not seg.desizaun_rbr:
			seg.desizaun_rbr = valor
			seg.save(update_fields=['desizaun_rbr'])


class Migration(migrations.Migration):
	dependencies = [('kazu', '0015_index_relatoriu')]
	operations = [migrations.RunPython(ba_desizaun, migrations.RunPython.noop)]
