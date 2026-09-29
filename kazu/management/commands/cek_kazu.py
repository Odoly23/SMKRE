from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Exists, OuterRef
from django.utils import timezone
from kazu.models import Kazu, KazuHistoria

# Kazu mosu iha portal públiku bainhira: aprovadu + konsentimentu + la marka "la publika"
PORTAL = ('APPROVED', 'COMPLETED')


class Command(BaseCommand):
	help = ("Haree kazu foun (web no HP) no nia dalan: haruka → verifika → aprova → portal. "
		"Lee deit, seguru iha production.")

	def add_arguments(self, parser):
		parser.add_argument('--loron', type=int, default=7, help='Kazu kria/atualiza iha loron N ikus (default 7)')
		parser.add_argument('--email', default='', help='Filtra tuir Investigadór (email)')
		parser.add_argument('--kode', default='', help='Kazu ida deit (kódigu SMKRE-...)')

	def naran(self, user):
		return user.username.split('@')[0] if user else '-'

	def handle(self, *args, **opt):
		qs = Kazu.objects.select_related('munisipiu', 'created_by', 'verified_by', 'approved_by').annotate(
			n_foto=Count('evidensia', filter=Q(evidensia__tipu='FOTO'), distinct=True),
			husi_hp=Exists(KazuHistoria.objects.filter(kazu=OuterRef('pk'), nota='SINKRON')),
		)
		if opt['kode']:
			qs = qs.filter(kode__iexact=opt['kode'].strip())
		else:
			qs = qs.filter(updated_at__gte=timezone.now() - timedelta(days=opt['loron'])).exclude(titulu__startswith='[DEMO]')
		if opt['email']:
			qs = qs.filter(created_by__username=opt['email'].strip().lower())
		qs = qs.order_by('-updated_at')[:50]
		if not qs:
			self.stdout.write(self.style.WARNING('La iha kazu foun iha períodu ne\'e.'))
			return

		self.stdout.write(f'{"KÓDIGU":<22} {"HUSI":<4} {"STATUS":<10} {"MUNISÍPIU":<12} {"FOTO":>4}  {"INVESTIGADÓR":<20} {"VERIFIKA":<18} {"APROVA":<18} PORTAL')
		for k in qs:
			portal = 'SIN' if (k.status in PORTAL and k.konsentimentu and not k.la_publika) else '-'
			self.stdout.write(f'{(k.kode or "(rascunho)"):<22} {"HP" if k.husi_hp else "WEB":<4} {k.status:<10} {k.munisipiu.name[:11]:<12} {k.n_foto:>4}  '
				f'{self.naran(k.created_by)[:19]:<20} {self.naran(k.verified_by)[:17]:<18} {self.naran(k.approved_by)[:17]:<18} {portal}')

		lista = list(qs)
		konta = lambda st: sum(1 for k in lista if k.status in st)
		self.stdout.write(self.style.SUCCESS(
			f'Total {len(lista)} · rascunho {konta(("DRAFT", "ONGOING", "PENDING"))} · hein verifika {konta(("SYNCED",))} · '
			f'verifikadu {konta(("VERIFIED",))} · aprovadu/remata {konta(PORTAL)} · rejeitadu {konta(("REJECTED",))}'))
		self.stdout.write('Portal públiku: DEBUG = kedas · production = atualiza kada minutu 10 (cache).')
