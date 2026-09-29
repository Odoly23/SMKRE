from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone
from kazu.models import Kazu, KazuHistoria


class Command(BaseCommand):
	help = "Haree kazu ne'ebé tama husi app offline (HP) — atu verifika sinkron servisu. Lee deit, seguru iha production."

	def add_arguments(self, parser):
		parser.add_argument('--loron', type=int, default=7, help='Kazu sinkron iha loron N ikus (default 7)')
		parser.add_argument('--email', default='', help='Filtra tuir Investigadór (email)')

	def handle(self, *args, **opt):
		desde = timezone.now() - timedelta(days=opt['loron'])
		ids = KazuHistoria.objects.filter(nota='SINKRON', created_at__gte=desde).values_list('kazu_id', flat=True)
		qs = Kazu.objects.filter(pk__in=ids).select_related('munisipiu', 'suku', 'created_by').annotate(
			n_foto=Count('evidensia', filter=Q(evidensia__tipu='FOTO'), distinct=True),
			n_video=Count('evidensia', filter=Q(evidensia__tipu='VIDEO'), distinct=True),
		).order_by('-updated_at')
		if opt['email']:
			qs = qs.filter(created_by__username=opt['email'].strip().lower())
		if not qs:
			self.stdout.write(self.style.WARNING(f'La iha kazu sinkron husi HP iha loron {opt["loron"]} ikus.'))
			return
		self.stdout.write(f'{"KÓDIGU":<24} {"STATUS":<10} {"FATIN":<26} {"GPS":<22} {"FOTO":>4} {"VÍDEO":>5}  INVESTIGADÓR / SINKRON')
		for k in qs:
			fatin = f'{k.suku or "-"}, {k.munisipiu}'[:25]
			gps = f'{k.latitude},{k.longitude}' if k.latitude is not None else '-'
			sinkron = timezone.localtime(k.synced_at).strftime('%d/%m %H:%M') if k.synced_at else 'seidauk haruka'
			self.stdout.write(f'{k.kode or "(seidauk iha kódigu)":<24} {k.status:<10} {fatin:<26} {gps[:21]:<22} {k.n_foto:>4} {k.n_video:>5}  {k.created_by.username} · {sinkron}')
		ok = qs.filter(status='SYNCED').count() + qs.exclude(status__in=['SYNCED', 'PENDING']).count()
		pendente = qs.filter(status='PENDING').count()
		self.stdout.write(self.style.SUCCESS(f'Total {qs.count()} kazu husi HP · {ok} kompletu'
			+ (f' · {pendente} seidauk haruka (evidénsia ka haruka falla — sinkron fali husi HP)' if pendente else '')))
