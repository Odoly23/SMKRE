from django.conf import settings
from django.db import migrations


def enxe_fokal(apps, schema_editor):
	# Kazu tuan: Fokal Point RbR = Investigadór ne'ebé kria kazu (se seidauk iha)
	Kazu = apps.get_model('kazu', 'Kazu')
	KazuSegimentu = apps.get_model('kazu', 'KazuSegimentu')
	PesoalUser = apps.get_model('users', 'PesoalUser')
	pesoal = {pu.user_id: pu.pesoal for pu in PesoalUser.objects.select_related('pesoal').exclude(user=None)}
	for kazu in Kazu.objects.select_related('created_by').iterator():
		seg, _c = KazuSegimentu.objects.get_or_create(kazu=kazu)
		if seg.fokal_naran:
			continue
		p, u = pesoal.get(kazu.created_by_id), kazu.created_by
		seg.fokal_naran = ((p.name if p else '') or u.username)[:150]
		seg.fokal_telemovel = ((p.phone if p else '') or '')[:50]
		seg.fokal_organizasaun = 'Rede ba Rai'
		seg.fokal_enderesu = getattr(settings, 'PORTAL_ENDERESU', '')[:255]
		seg.fokal_tipu = seg.fokal_tipu or 'SEKRETARIADU'
		seg.save()


class Migration(migrations.Migration):
	dependencies = [
		('kazu', '0007_followup'),
		('users', '0002_pesoal_uuid'),
	]
	operations = [migrations.RunPython(enxe_fokal, migrations.RunPython.noop)]
