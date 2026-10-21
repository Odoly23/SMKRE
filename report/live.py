"""Dadus ba ekran Live: agregadu no anónimu de'it (la iha naran, kontaktu ka testu nota).
Cache segundu 20: ekran barak ka atualiza beibeik la todan server."""
from datetime import timedelta
from django.core.cache import cache
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth, TruncDate, Coalesce
from django.utils import timezone
from django.utils.translation import gettext as _

CACHE_SEG = 20
FULAN = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def _kazu():
	from kazu.models import Kazu, DRAFT, ONGOING, PENDING, CANCELED
	return Kazu.objects.exclude(status__in=[DRAFT, ONGOING, PENDING, CANCELED])


def _atividade(limit=14):
	# Eventu ikus: kódigu + munisípiu + saida mak akontese (anónimu)
	from kazu.models import KazuHistoria, STATUS_KAZU_CHOICES
	from legal.models import SurveiLegal
	testu = {
		'SYNCED': (_('Kazu foun simu'), 'foun'), 'VERIFIED': (_('Kazu verifikadu'), 'ok'),
		'APPROVED': (_('Kazu aprovadu'), 'ok'), 'REJECTED': (_('Kazu fila ba hadia'), 'alerta'),
		'COMPLETED': (_('Kazu remata'), 'ok'), 'FOLLOWUP': (_('Follow-up ba terrenu'), 'info'),
	}
	status_kazu = dict(STATUS_KAZU_CHOICES)
	ev = []
	hist = KazuHistoria.objects.filter(Q(tipu=KazuHistoria.DADUS, status_foun__in=list(testu)) | Q(tipu=KazuHistoria.KAZU)) \
		.select_related('kazu__munisipiu').order_by('-created_at')[:limit]
	for h in hist:
		if h.tipu == KazuHistoria.KAZU:
			t, k = _('Status kazu: %(s)s') % {'s': status_kazu.get(h.status_foun, h.status_foun)}, 'info'
		else:
			t, k = testu[h.status_foun]
		ev.append({'tempu': h.created_at, 'testu': t, 'kode': h.kazu.kode or '', 'fatin': h.kazu.munisipiu.name if h.kazu.munisipiu_id else '', 'tipu': k})
	for s in SurveiLegal.objects.exclude(haruka_at=None).select_related('munisipiu').order_by('-haruka_at')[:6]:
		ev.append({'tempu': s.haruka_at, 'testu': _('Survei legál foun'), 'kode': s.kode or '', 'fatin': s.munisipiu.name, 'tipu': 'legal'})
		if s.verified_at:
			ev.append({'tempu': s.verified_at, 'testu': _('Survei legál verifikadu'), 'kode': s.kode or '', 'fatin': s.munisipiu.name, 'tipu': 'ok'})
	ev.sort(key=lambda e: e['tempu'], reverse=True)
	return [dict(e, tempu=timezone.localtime(e['tempu']).isoformat()) for e in ev[:limit]]


def kalkula():
	from custom.models import Munisipiu, TipuKonflitu
	from kazu.models import UmaKainAfetada, STATUS_KAZU_CHOICES, SYNCED, VERIFIED, APPROVED, COMPLETED, AKSAUN_LEGAL
	from legal.models import NotaLegal, SurveiLegal
	from legal.services import KAZU_STATUS_LEGAL
	from report.utils import STATUS_AKTIVU, eviksaun_aktivu
	agora = timezone.localtime()
	hoje = agora.date()
	kazu = _kazu()
	verifikadu = kazu.filter(status__in=[VERIFIED, APPROVED, COMPLETED, 'FOLLOWUP'])
	afe = UmaKainAfetada.objects.filter(kazu__in=kazu).aggregate(uk=Sum('uma_kain'), ema=Sum('total_ema'))
	semana = hoje - timedelta(days=hoje.weekday())
	kpi = {
		'total': kazu.count(),
		'verifikadu': verifikadu.count(),
		'hein': kazu.filter(status=SYNCED).count(),
		'aktivu': kazu.filter(status__in=STATUS_AKTIVU).count(),
		'eviksaun': eviksaun_aktivu(kazu).count(),
		'urjente': kazu.filter(urjente=True, status__in=STATUS_AKTIVU).count(),
		'uma_kain': afe['uk'] or 0,
		'ema': afe['ema'] or 0,
		'legal': kazu.filter(status_kazu=AKSAUN_LEGAL).count(),
		'survei_hein': SurveiLegal.objects.filter(status=SurveiLegal.HARUKA).count(),
		'semana': kazu.filter(created_at__date__gte=semana).count(),
		'semana_kotuk': kazu.filter(created_at__date__gte=semana - timedelta(days=7), created_at__date__lt=semana).count(),
	}
	# Tendénsia fulan 12 (data simu kazu; mamuk → data kria)
	hahu = (hoje.replace(day=1) - timedelta(days=330)).replace(day=1)
	data_kazu = kazu.annotate(d=Coalesce('data_relatoriu', TruncDate('created_at')))
	por_fulan = dict(data_kazu.filter(d__gte=hahu).annotate(f=TruncMonth('d')).values('f').annotate(n=Count('pk')).values_list('f', 'n'))
	por_fulan = {(k.year, k.month): v for k, v in por_fulan.items() if k}
	fulan, y, m = [], hahu.year, hahu.month
	for _i in range(12):
		fulan.append({'label': f'{FULAN[m - 1]} {str(y)[2:]}', 'n': por_fulan.get((y, m), 0)})
		m += 1
		if m > 12:
			y, m = y + 1, 1
	mun_n = dict(kazu.values_list('munisipiu').annotate(n=Count('pk')).values_list('munisipiu', 'n'))
	mun = [{'code': mm.code, 'name': mm.name, 'n': mun_n.get(mm.pk, 0)} for mm in Munisipiu.active.all()]
	tipu = [{'name': t.name, 'n': t.n} for t in TipuKonflitu.active.annotate(n=Count('kazu', filter=Q(kazu__in=kazu), distinct=True)).order_by('-n') if t.n]
	sk_n = dict(kazu.values_list('status_kazu').annotate(n=Count('pk')).values_list('status_kazu', 'n'))
	status_kazu = [{'name': str(l), 'code': c, 'n': sk_n.get(c, 0)} for c, l in STATUS_KAZU_CHOICES]
	# Mapa: kazu ho GPS (kódigu + munisípiu de'it); foun = loron 7 ikus
	pontu = [{'lat': float(k.latitude), 'lng': float(k.longitude), 'kode': k.kode or '', 'fatin': k.munisipiu.name,
		'urjente': k.urjente, 'foun': k.created_at >= agora - timedelta(days=7)}
		for k in kazu.exclude(latitude=None).exclude(longitude=None).select_related('munisipiu').order_by('-created_at')[:600]]
	prazu = [{'kode': n.kazu.kode or '', 'tipu': n.get_tipu_display(), 'data': n.prazu.isoformat(), 'loron': (n.prazu - hoje).days}
		for n in NotaLegal.objects.filter(remata=False, prazu__gte=hoje - timedelta(days=30), prazu__lte=hoje + timedelta(days=14),
			kazu__status__in=KAZU_STATUS_LEGAL).select_related('kazu').order_by('prazu')[:8]]
	return {
		'agora': agora.isoformat(), 'kpi': kpi, 'fulan': fulan, 'mun': mun, 'tipu': tipu[:8], 'status_kazu': status_kazu,
		'pontu': pontu, 'prazu': prazu, 'atividade': _atividade(),
	}


def dadus():
	d = cache.get('report-live')
	if d is None:
		d = kalkula()
		cache.set('report-live', d, CACHE_SEG)
	return d
