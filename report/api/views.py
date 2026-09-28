from collections import OrderedDict
from datetime import date
from django.db.models import Count, Sum, Q
from django.utils.translation import gettext as _
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from config.permissions import HasRole
from config.rbac import ROLE_DASHBOARD
from custom.models import Munisipiu, TipuKonflitu
from kazu.models import UmaKainAfetada, STATUS_CHOICES
from report.utils import report_queryset, STATUS_RELATORIU, DESLOKAMENTU


class _ReportAPI(APIView):
	authentication_classes = [SessionAuthentication]
	permission_classes = [IsAuthenticated, HasRole(*ROLE_DASHBOARD)]


class APIKazuMun(_ReportAPI):
	def get(self, request, format=None):
		label, obj = list(), list()
		kazu = report_queryset(request)
		muns = Munisipiu.active.all()
		for m in muns:
			k = kazu.filter(munisipiu=m).count()
			label.append(m.name)
			obj.append(k)
		data = {'label': label, 'obj': obj}
		return Response(data)


class APIKazuTipu(_ReportAPI):
	def get(self, request, format=None):
		label, obj = list(), list()
		kazu = report_queryset(request)
		for t in TipuKonflitu.active.all():
			label.append(t.name)
			obj.append(kazu.filter(tipu_konflitu=t).count())
		return Response({'label': label, 'obj': obj})


class APIKazuStatus(_ReportAPI):
	def get(self, request, format=None):
		label, obj = list(), list()
		kazu = report_queryset(request)
		status_label = dict(STATUS_CHOICES)
		for s in STATUS_RELATORIU:
			label.append(str(status_label[s]))
			obj.append(kazu.filter(status=s).count())
		return Response({'label': label, 'obj': obj, 'code': STATUS_RELATORIU})


class APIKazuTendensia(_ReportAPI):
	# Tendénsia: kazu kada fulan (fulan 12 ikus) — total no deslokamentu/eviksaun
	def get(self, request, format=None):
		kazu = report_queryset(request).exclude(data_relatoriu=None)
		hoje = date.today()
		months = OrderedDict()
		y, m = hoje.year, hoje.month
		for _i in range(12):
			months[(y, m)] = [0, 0]
			m -= 1
			if m == 0:
				y, m = y - 1, 12
		months = OrderedDict(reversed(list(months.items())))
		first = list(months.keys())[0]
		rows = kazu.filter(data_relatoriu__gte=date(first[0], first[1], 1)).values_list('data_relatoriu', 'pk').distinct()
		evik = set(kazu.filter(Q(tipu_konflitu__code=DESLOKAMENTU) | Q(insidente__isnull=False)).values_list('pk', flat=True))
		for d, pk in rows:
			key = (d.year, d.month)
			if key in months:
				months[key][0] += 1
				if pk in evik:
					months[key][1] += 1
		label = [f'{mm:02d}/{yy}' for (yy, mm) in months.keys()]
		return Response({'label': label, 'total': [v[0] for v in months.values()], 'eviksaun': [v[1] for v in months.values()]})


class APIAfetadu(_ReportAPI):
	# Populasaun afetada tuir munisípiu (stacked)
	def get(self, request, format=None):
		kazu = report_queryset(request)
		afetadu = UmaKainAfetada.objects.filter(kazu__in=kazu)
		label, mane, feto, labarik = [], [], [], []
		for m in Munisipiu.active.all():
			r = afetadu.filter(kazu__munisipiu=m).aggregate(mane=Sum('mane'), feto=Sum('feto'), labarik=Sum('labarik'))
			label.append(m.name)
			mane.append(r['mane'] or 0)
			feto.append(r['feto'] or 0)
			labarik.append(r['labarik'] or 0)
		return Response({'label': label, 'mane': mane, 'feto': feto, 'labarik': labarik})


class APIMapa(_ReportAPI):
	# Mapa: total tuir munisípiu (hotspot) + pin kada kazu (koordenada GPS)
	def get(self, request, format=None):
		kazu = report_queryset(request)
		mun = {r['munisipiu__code']: r['n'] for r in kazu.order_by().values('munisipiu__code').annotate(n=Count('id', distinct=True))}   # order_by(): la tama iha GROUP BY
		munisipiu = [{'code': m.code, 'name': m.name, 'lat': float(m.latitude) if m.latitude else None,
			'lng': float(m.longitude) if m.longitude else None, 'total': mun.get(m.code, 0)} for m in Munisipiu.active.all()]
		status_label = dict(STATUS_CHOICES)
		pins = []
		for k in kazu.exclude(latitude=None).select_related('munisipiu', 'suku').prefetch_related('tipu_konflitu', 'afetadu')[:3000]:
			pins.append({
				'id': str(k.pk), 'kode': k.kode, 'lat': float(k.latitude), 'lng': float(k.longitude),
				'suku': k.suku.name if k.suku else '', 'munisipiu': k.munisipiu.name,
				'tipu': ', '.join(t.name for t in k.tipu_konflitu.all()),
				'uma_kain': k.total_uma_kain, 'status': str(status_label[k.status]), 'urjente': k.urjente,
			})
		return Response({'munisipiu': munisipiu, 'pins': pins, 'label_detalla': _('Haree Detalla')})
