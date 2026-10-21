"""
Import kazu husi Excel (Admin deit).

	1. Admin download template (aba "Kazu" + aba lista kódigu)
	2. Upload → lee → valida kada liña → pratinjau (KazuImport RASCUNHO, la kria kazu)
	3. Konfirma → kria kazu ho status "Hein Verifikasaun" (fluxu hanesan: Admin verifika, Superadmin aprova)

Koordenada mamuk ka la kompletu → fatin aproksimadu (sentru suku, ka munisípiu) + marka gps_aproksimadu;
Admin hadia iha mapa (marka bele dada). Konsentimentu mamuk = LAE → kazu la tama portal públiku.
"""
import hashlib
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from config.rbac import SUPERADMIN
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia, TipuKonflitu, TipuRai
from kazu import airtable
from kazu.forms import TL_LAT, TL_LON
from kazu.models import Kazu, KazuHistoria, KazuImport, KazuSegimentu, UmaKainAfetada, SYNCED, VERIFIED
from kazu.services import generate_kode, _historia
from notification.utils import kirim_notif_role

MAX_LINA = 500
MAX_BYTES = 5 * 1024 * 1024
SIN = {'SIN', 'S', 'YES', 'Y', 'SIM', 'YA', '1', 'TRUE', 'LOOS'}

# (kolun, deskrisaun ba template, obrigatóriu)
KOLUN = [
	('data_relatoriu', 'Data simu kazu iha RbR (AAAA-MM-LL)', True),
	('munisipiu', 'Munisípiu (kódigu ka naran)', True),
	('postu', 'Postu (kódigu ka naran)', False),
	('suku', 'Suku (kódigu ka naran)', False),
	('aldeia', 'Aldeia (kódigu ka naran)', False),
	('latitude', 'Latitude (ex. -8.5586)', False),
	('longitude', 'Longitude (ex. 125.5736)', False),
	('data_akontesimentu', 'Data akontesimentu (AAAA-MM-LL)', False),
	('tipu_konflitu', 'Tipu konflitu (kódigu, separa ho ;)', True),
	('tipu_seluk', 'Tipu "Seluk": esplika', False),
	('tipu_rai', 'Tipu rai (kódigu)', False),
	('deskrisaun', 'Observasaun kona-ba tipu kazu', False),
	('uma_kain', 'Uma-kain afetada', False),
	('mane', 'Mane', False),
	('feto', 'Feto', False),
	('labarik', 'Labarik', False),
	('total_ema', 'Total ema', False),
	('katuas_ferik', 'Idozu (tinan 60 ba leten)', False),
	('defisiensia', 'Ema ho defisiénsia', False),
	('konsentimentu', 'Konsentimentu (SIN / LAE)', False),
	('la_publika', 'La publika iha portal (SIN / LAE)', False),
	('titulu', 'Naran kazu', False),
	('observasaun', 'Observasaun', False),
]
# Pergunta formuláriu RbR (Airtable): kolun ho naran field; valór konverte tuir tipu field iha modelu
KAMPU_KAZU_RBR = ['tinan_disputa_hahu', 'projetu', 'entidade_foti', 'entidade_kategoria', 'entidade_kategoria_seluk', 'enderesu_fatin', 'rai_luan',
	'rai_luan_unidade', 'iha_dadus_uma_kain', 'fonte_dadus_uma_kain', 'observasaun_afetadu', 'eviksaun_akontese', 'data_eviksaun',
	'konsultasaun_molok', 'notifikasaun_klaru', 'uza_forsa', 'observasaun_eviksaun', 'portavos_naran', 'portavos_kontaktu',
	'portavos_observasaun']
KAMPU_SEGIMENTU = [f.name for f in KazuSegimentu._meta.get_fields()
	if getattr(f, 'concrete', False) and f.name not in ('id', 'kazu', 'updated_by', 'updated_at')]


def _deskr(model, campo):
	f = model._meta.get_field(campo)
	opsaun = ' / '.join(str(l) for _c, l in f.choices) if f.choices else ''
	tipu = {'DateField': ' (AAAA-MM-LL)'}.get(f.get_internal_type(), '')
	return f'{f.verbose_name}{tipu}' + (f' — {opsaun}' if opsaun else '')


KOLUN += [(c, _deskr(Kazu, c), False) for c in KAMPU_KAZU_RBR]
KOLUN += [(c, _deskr(KazuSegimentu, c), False) for c in KAMPU_SEGIMENTU]
NARAN_KOLUN = [k[0] for k in KOLUN]


# ══════════════ 1. Template ══════════════
def template_excel():
	"""Template ho kabesallu hanesan baze dadus sentrál RbR (Airtable "Kazu Hotu") + lista opsaun."""
	from openpyxl.utils import get_column_letter
	wb = Workbook()
	ws = wb.active
	ws.title = 'Kazu Hotu'
	kab = PatternFill('solid', fgColor='0B4F3C')
	obrig = PatternFill('solid', fgColor='0E8A68')
	presiza = {'Munisipiu', 'Tipu Kazu'}
	ws.append(airtable.KABESALLU)
	for i, h in enumerate(airtable.KABESALLU, start=1):
		c = ws.cell(row=1, column=i)
		c.font, c.fill = Font(bold=True, color='FFFFFF'), (obrig if h in presiza else kab)
		ws.column_dimensions[get_column_letter(i)].width = 24
	ezemplu = {airtable.H_ID: 'RBR/999_2026_Ezemplu (hamoos liña ne\'e)', airtable.H_REF: 'RBR/999', 'Tinan Kazu Hahu': 2019,
		'Data Simu Kazu iha RBR': '15/09/2026', 'Kazu': 'Ezemplu kazu', 'Tipu Kazu': 'Governu hasai komunidade husi rai estadu',
		'Munisipiu': 'Liquiçá', 'Suku': 'Dato', 'Dadus Uma Kain iha ka lae?': 'Iha', 'Uma Kain afetadu hira': 12, 'Total Ema': 58,
		'Feto ': 28, 'Mane': 30, 'Eviksaun Akontese ona?': 'Lae', 'Status Kazu': 'Seidauk resolve', "RBR nia desizaun ba Kazu ne'e": 'Monitorizasaun',
		'Pontu Kordenadu (GPS)': '-8.5871, 125.3410'}
	ws.append([ezemplu.get(h, '') for h in airtable.KABESALLU])
	for c in ws[2]:
		c.font = Font(color='9AA59F')
	ws.freeze_panes = 'B2'

	# Aba lista (naran ne'ebé sistema rekoñese) + dropdown
	def aba(naran, kab_list, rows):
		w = wb.create_sheet(naran)
		w.append(kab_list)
		for c in w[1]:
			c.font, c.fill = Font(bold=True, color='FFFFFF'), kab
		for r in rows:
			w.append(list(r))
		for col in w.columns:
			w.column_dimensions[col[0].column_letter].width = 28
		return w
	aba('Munisipiu', ['naran', 'code'], Munisipiu.active.values_list('name', 'code'))
	aba('Postu', ['naran', 'munisipiu'], PostuAdministrativu.active.values_list('name', 'munisipiu__name'))
	aba('Suku', ['naran', 'postu', 'munisipiu'], Suku.active.values_list('name', 'postu__name', 'postu__munisipiu__name'))
	opsaun = {'Tipu Kazu': [n for n in TipuKonflitu.active.values_list('name', flat=True)], 'Verified': ['checked']}
	for h, campo in airtable.OPSAUN.items():
		model = Kazu if hasattr(Kazu, campo) else KazuSegimentu
		opsaun[h] = [str(l) for _c, l in model._meta.get_field(campo).choices]
	opsaun['Dadus Uma Kain iha ka lae?'] = ['Iha', 'Laiha', 'La hatene']
	aba_ops = wb.create_sheet('Opsaun')
	n_mun = Munisipiu.active.count() + 1
	validasaun = {'Munisipiu': f'=Munisipiu!$A$2:$A${n_mun}'}
	for i, (h, lista) in enumerate(opsaun.items(), start=1):
		letra = get_column_letter(i)
		aba_ops.cell(row=1, column=i, value=h).font = Font(bold=True)
		for j, label in enumerate(lista, start=2):
			aba_ops.cell(row=j, column=i, value=label)
		validasaun[h] = f'=Opsaun!${letra}$2:${letra}${len(lista) + 1}'
	for h, formula in validasaun.items():
		dv = DataValidation(type='list', formula1=formula, allow_blank=True, showErrorMessage=False)
		ws.add_data_validation(dv)
		kol = get_column_letter(airtable.KABESALLU.index(h) + 1)
		dv.add(f'{kol}2:{kol}{MAX_LINA + 1}')
	buf = BytesIO()
	wb.save(buf)
	return buf.getvalue()


# ══════════════ 2. Lee no valida ══════════════
def lee_excel(f):
	# Retorna (naran_file, sha256, liña sira [{kolun: valór}]) ka ValidationError
	if f.size > MAX_BYTES:
		raise ValidationError(_('File boot liu (máximu 5 MB).'))
	raw = f.read()
	rows = _lee_rows(f.name, raw)
	if not rows:
		raise ValidationError(_('File mamuk.'))
	# Formatu baze dadus sentrál RbR (Airtable "Kazu Hotu"): kabesallu orijinál
	if airtable.e_airtable(rows[0]):
		kab = [str(c or '').strip() for c in rows[0]]
		lina = []
		for n, r in enumerate(rows[1:], start=2):
			row = dict(zip(kab, r))
			if not airtable.iha_dadus(row):              # rejistu Airtable mamuk (ID automátiku de'it)
				continue
			d = airtable.lina_interna(row)
			d['_lina'] = n
			lina.append(d)
		if len(lina) > MAX_LINA:
			raise ValidationError(_('Liña barak liu (máximu %(n)s). Fahe ba file barak.') % {'n': MAX_LINA})
		return f.name[:255], hashlib.sha256(raw).hexdigest(), lina
	kab = [str(c or '').strip().lower() for c in rows[0]]
	if 'munisipiu' not in kab:
		raise ValidationError(_('Kolun la tuir template (presiza "munisipiu"…). Download template.'))
	lina = []
	for n, r in enumerate(rows[1:], start=2):
		d = {k: v for k, v in zip(kab, r) if k in NARAN_KOLUN}
		if not any(v not in (None, '') for v in d.values()):
			continue
		if n == 2 and str(d.get('data_relatoriu') or '').startswith('Data relat'):
			continue                                    # liña esplikasaun template
		d['_lina'] = n
		lina.append(d)
	if len(lina) > MAX_LINA:
		raise ValidationError(_('Liña barak liu (máximu %(n)s). Fahe ba file barak.') % {'n': MAX_LINA})
	return f.name[:255], hashlib.sha256(raw).hexdigest(), lina


def _lee_rows(naran, raw):
	# .xlsx (aba "Kazu" ka dahuluk) ka .csv (UTF-8 / Excel Windows)
	if naran.lower().endswith('.csv'):
		import csv
		import io
		for kodifika in ('utf-8-sig', 'cp1252'):
			try:
				testu = raw.decode(kodifika)
				break
			except UnicodeDecodeError:
				continue
		else:
			raise ValidationError(_('Labele lee file CSV ne\'e.'))
		return [tuple(r) for r in csv.reader(io.StringIO(testu, newline=''))]
	if not naran.lower().endswith('.xlsx') or raw[:2] != b'PK':
		raise ValidationError(_('File tenke Excel .xlsx ka .csv (uza template ka export Airtable).'))
	try:
		wb = load_workbook(BytesIO(raw), read_only=True, data_only=True)
	except Exception:
		raise ValidationError(_('Labele lee file Excel ne\'e.'))
	ws = wb['Kazu'] if 'Kazu' in wb.sheetnames else wb.worksheets[0]
	return list(ws.iter_rows(values_only=True))


def _testu(v):
	return '' if v is None else str(v).strip()


def _data(v):
	if v in (None, ''):
		return None
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	t = _testu(v)
	for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
		try:
			return datetime.strptime(t, fmt).date()
		except ValueError:
			pass
	raise ValueError(t)


def _int(v):
	if v in (None, ''):
		return None
	n = int(float(str(v).replace(',', '.')))
	if n < 0:
		raise ValueError(v)
	return n


def _dec(v):
	if v in (None, ''):
		return None
	return Decimal(str(v).replace(',', '.').strip()).quantize(Decimal('0.000001'))


def _normal(t):
	# La sensível ba aksentu, espasu, pontuasaun (ex. "Claim balu resolve balu seidauk" = "Claim balu resolve, balu seidauk")
	return airtable.normal(t)


def _konverte(model, campo, raw):
	# Valór Excel → valór JSON (string / númeru) tuir tipu field; ValueError bainhira la validu
	f = model._meta.get_field(campo)
	if raw in (None, ''):
		return None
	if f.choices:
		alvu = _normal(raw)
		for code, label in f.choices:
			if alvu in (_normal(code), _normal(label)):
				return code
		raise ValueError(raw)
	tipu = f.get_internal_type()
	if tipu == 'DateField':
		return _data(raw).isoformat()
	if tipu in ('PositiveSmallIntegerField', 'PositiveIntegerField', 'IntegerField'):
		return _int(raw)
	if tipu == 'DecimalField':
		return str(_dec(raw))
	return _testu(raw)[:f.max_length] if f.max_length else _testu(raw)


def _kampu_extra(model, campos, d, erru, avizu=None):
	# avizu (dadus Airtable tuan): valór la validu → avizu, kampu mamuk (la blokeia liña)
	out = {}
	nomes = {f.name for f in model._meta.get_fields()}
	for campo in campos:
		# Opsaun ho "Seluk" + kampu esplika: "Seluk: testu" ka valór la koñesidu → SELUK + testu
		if f'{campo}_seluk' in nomes and _testu(d.get(campo)):
			raw = _testu(d.get(campo))
			kab, _sep, rest = raw.partition(':')
			try:
				_konverte(model, campo, raw)
			except ValueError:
				if _normal(kab) == _normal('Seluk'):
					out[campo], out[f'{campo}_seluk'] = 'SELUK', rest.strip()[:255]
				else:
					out[campo], out[f'{campo}_seluk'] = 'SELUK', raw[:255]
				continue
		if campo.endswith('_seluk') and campo in out:
			continue
		try:
			v = _konverte(model, campo, d.get(campo))
		except (ValueError, TypeError, InvalidOperation):
			msg = _('"%(c)s": valór "%(v)s" la validu.') % {'c': model._meta.get_field(campo).verbose_name, 'v': _testu(d.get(campo))}
			(avizu if avizu is not None else erru).append(msg)
			continue
		if v is not None:
			out[campo] = v
	return out


class _Buka:
	# Buka objetu husi kódigu ka naran (la sensível ba letra boot/kiik)
	def __init__(self, qs):
		self.code = {o.code.upper(): o for o in qs}
		self.naran = {}
		for o in qs:
			self.naran.setdefault(_normal(o.name), []).append(o)     # "Ataúro" = "Atauro", "Cristo Rei " = "Cristo Rei"

	def __call__(self, v, filtru=None):
		t = _testu(v).upper()
		if not t:
			return None
		o = self.code.get(t)
		if o:
			return o
		opsaun = [x for x in self.naran.get(_normal(t), []) if not filtru or filtru(x)]
		if not opsaun:                                  # "Oecusse" → "Oé-Cusse Ambeno (RAEOA)" (naran badak)
			n = _normal(t)
			opsaun = [x for k, xs in self.naran.items() if len(n) >= 4 and k.startswith(n) for x in xs if not filtru or filtru(x)]
		return opsaun[0] if len(opsaun) == 1 else False   # False = la hetan ka naran duplikadu

	def besik(self, v, filtru=None, korte=0.82):
		# Naran hakerek la hanesan (ex. "Akadirihun" / "Acadiruhun"): kandidatu ida ne'ebé besik liu
		import difflib
		n = _normal(v)
		kand = {k: xs for k, xs in self.naran.items() if any(not filtru or filtru(x) for x in xs)}
		hetan = difflib.get_close_matches(n, list(kand), n=2, cutoff=korte)
		if len(hetan) == 1 or (len(hetan) == 2 and difflib.SequenceMatcher(None, n, hetan[0]).ratio() > difflib.SequenceMatcher(None, n, hetan[1]).ratio()):
			xs = [x for x in kand[hetan[0]] if not filtru or filtru(x)]
			return xs[0] if len(xs) == 1 else None
		return None


def valida(lina):
	# Kada liña: {'lina', 'ok', 'erru': [...], 'avizu': [...], 'dadus': {... id/valór ba kria}, 'rezumu': {...}}
	buka_mun = _Buka(list(Munisipiu.active.all()))
	buka_postu = _Buka(list(PostuAdministrativu.active.select_related('munisipiu')))
	buka_suku = _Buka(list(Suku.active.select_related('postu')))
	buka_aldeia = _Buka(list(Aldeia.active.select_related('suku')))
	buka_tipu = _Buka(list(TipuKonflitu.active.all()))
	buka_rai = _Buka(list(TipuRai.active.all()))
	hoje = timezone.localdate()
	haree = set()
	ref_iha = set(Kazu.objects.exclude(referensia_rbr=None).values_list('referensia_rbr', flat=True))
	rezultadu = []
	for d in lina:
		erru, avizu, out = [], list(d.get('_avizu', [])), {}
		at = d.get('_airtable', False)               # dadus Airtable tuan: lokalizasaun / data la kompletu = avizu

		# Data
		for campo, label in (('data_relatoriu', _('Data relatóriu')), ('data_akontesimentu', _('Data akontesimentu'))):
			try:
				out[campo] = _data(d.get(campo))
			except ValueError:
				erru.append(_('%(c)s la validu (uza AAAA-MM-LL).') % {'c': label})
				out[campo] = None
		if not out['data_relatoriu'] and not any(_('Data relatóriu') in e for e in erru):
			(avizu if at else erru).append(_('Data relatóriu obrigatóriu.') if not at else _('Data simu kazu la iha.'))
		if out['data_relatoriu'] and out['data_relatoriu'] > hoje:
			erru.append(_('Data relatóriu labele iha futuru.'))
		if out['data_relatoriu'] and out['data_akontesimentu'] and out['data_akontesimentu'] > out['data_relatoriu']:
			erru.append(_('Data akontesimentu labele liu data relatóriu.'))

		# Lokalizasaun (tenke tuir malu)
		mun = buka_mun(d.get('munisipiu'))
		if not mun:
			erru.append(_('Munisípiu "%(v)s" la hetan.') % {'v': _testu(d.get('munisipiu'))} if _testu(d.get('munisipiu')) else _('Munisípiu obrigatóriu.'))
		postu = buka_postu(d.get('postu'), lambda o: mun and o.munisipiu_id == mun.pk)
		f_suku = lambda o: (not postu or o.postu_id == postu.pk) and (not mun or o.postu.munisipiu_id == mun.pk)
		suku = buka_suku(d.get('suku'), f_suku)
		if suku is False and at and mun:                # Airtable: postu tuan (DM 31/2026 muda postu) → buka iha munisípiu
			f_mun = lambda o: o.postu.munisipiu_id == mun.pk
			suku = buka_suku(d.get('suku'), f_mun)
			if suku is False:                           # naran hakerek la hanesan → besik liu iha munisípiu
				suku = buka_suku.besik(d.get('suku'), f_mun) or False
				if suku:
					avizu.append(_('Suku "%(v)s" → %(s)s (naran besik; haree loos ka lae).') % {'v': _testu(d.get('suku')), 's': suku.name})
			if suku and postu and suku.postu_id != postu.pk:
				postu = suku.postu                          # postu tuir suku (divizaun foun)
		# Aldeia: iha suku ne'ebé hetan; la iha suku → aldeia úniku iha munisípiu (suku/postu tuir aldeia)
		aldeia = buka_aldeia(d.get('aldeia'), lambda o: (o.suku_id == suku.pk) if suku else bool(mun and o.suku.postu.munisipiu_id == mun.pk))
		if aldeia and not suku:
			suku = aldeia.suku
			postu = postu if (postu and suku.postu_id == postu.pk) else suku.postu
		la_hetan = []
		for obj, campo, label in ((postu, 'postu', _('Postu')), (suku, 'suku', _('Suku')), (aldeia, 'aldeia', _('Aldeia'))):
			if obj is False:
				msg = _('%(c)s "%(v)s" la hetan (ka naran duplikadu: uza kódigu).') % {'c': label, 'v': _testu(d.get(campo))}
				if at:                                  # Airtable: rai naran orijinál iha enderesu, Admin hadia depois
					avizu.append(msg)
					la_hetan.append(f'{label}: {_testu(d.get(campo))}')
				else:
					erru.append(msg)
		if at:
			postu, suku, aldeia = (postu or None), (suku or None), (aldeia or None)
			if la_hetan:
				d['enderesu_fatin'] = ' · '.join(filter(None, [_testu(d.get('enderesu_fatin'))] + la_hetan))[:255]
		if mun and postu and postu.munisipiu_id != mun.pk:
			erru.append(_('Postu la iha munisípiu ne\'e.'))
		if postu and suku and suku.postu_id != postu.pk:
			erru.append(_('Suku la iha postu ne\'e.'))
		if suku and not postu:
			postu = suku.postu                              # postu husi suku
		if suku and aldeia and aldeia.suku_id != suku.pk:
			erru.append(_('Aldeia la iha suku ne\'e.'))

		# GPS: kompletu no iha Timor-Leste; se lae → fatin aproksimadu
		lat = lon = None
		try:
			lat, lon = _dec(d.get('latitude')), _dec(d.get('longitude'))
		except (InvalidOperation, ValueError):
			avizu.append(_('Koordenada la validu — uza fatin aproksimadu.'))
		if (lat is None) != (lon is None):
			avizu.append(_('Koordenada la kompletu — uza fatin aproksimadu.'))
			lat = lon = None
		if lat is not None and not (TL_LAT[0] <= lat <= TL_LAT[1] and TL_LON[0] <= lon <= TL_LON[1]):
			avizu.append(_('Koordenada li\'ur Timor-Leste — uza fatin aproksimadu.'))
			lat = lon = None
		aproksimadu = lat is None
		if aproksimadu and mun:
			sentru = suku if suku and suku.latitude is not None else mun
			if sentru.latitude is None:
				erru.append(_('Koordenada mamuk no munisípiu la iha sentru: hatama latitude/longitude.'))
			else:
				lat, lon = sentru.latitude, sentru.longitude
				if not any('aproksimadu' in a for a in avizu):
					avizu.append(_('Koordenada mamuk — uza sentru %(f)s. Hadia iha mapa hafoin import.') % {'f': sentru.name})

		# Tipu konflitu (kódigu barak, separa ho ; ka ,)
		tipu = []
		for t in [x for x in _testu(d.get('tipu_konflitu')).replace(',', ';').split(';') if x.strip()]:
			o = buka_tipu(t)
			if o:
				tipu.append(o)
			else:
				erru.append(_('Tipu konflitu "%(v)s" la hetan.') % {'v': t.strip()})
		if not tipu and not any(_('Tipu konflitu') in e for e in erru):
			erru.append(_('Tipu konflitu obrigatóriu.'))
		if any(t.presiza_esplika for t in tipu) and not _testu(d.get('tipu_seluk')):
			erru.append(_('Favor esplika tipu konflitu "Seluk".'))
		rai = buka_rai(d.get('tipu_rai'))
		if rai is False:
			erru.append(_('Tipu rai "%(v)s" la hetan.') % {'v': _testu(d.get('tipu_rai'))})

		deskrisaun = _testu(d.get('deskrisaun'))         # Observasaun kona-ba tipu kazu (opsionál)

		# Populasaun
		pop = {}
		for campo in ('uma_kain', 'mane', 'feto', 'labarik', 'total_ema', 'katuas_ferik', 'defisiensia'):
			try:
				pop[campo] = _int(d.get(campo))
			except (ValueError, TypeError):
				erru.append(_('"%(c)s" tenke númeru pozitivu.') % {'c': campo})
				pop[campo] = None

		konsentimentu = _testu(d.get('konsentimentu')).upper() in SIN
		if not konsentimentu:
			avizu.append(_('La iha konsentimentu — kazu la sei mosu iha portal públiku.'))

		# Duplikadu: referénsia RBR (Airtable) ka munisípiu + data + observasaun
		ref = d.get('_referensia')
		if ref and ref in ref_iha:
			erru.append(_('Referénsia %(r)s iha sistema ona (import ona).') % {'r': ref})
		if ref:
			ref_iha.add(ref)
		chave = (mun.pk if mun else None, out['data_relatoriu'], deskrisaun[:80].upper(), ref)
		if chave in haree:
			avizu.append(_('Liña hanesan iha file ne\'e (duplikadu?).'))
		haree.add(chave)
		if mun and out['data_relatoriu'] and Kazu.objects.filter(munisipiu=mun, data_relatoriu=out['data_relatoriu'], deskrisaun__iexact=deskrisaun).exists():
			avizu.append(_('Kazu hanesan iha sistema ona (duplikadu?).'))

		rezultadu.append({
			'lina': d['_lina'], 'ok': None, 'erru': erru, 'avizu': avizu,
			'dadus': {
				'titulu': _testu(d.get('titulu'))[:200],
				'data_relatoriu': out['data_relatoriu'].isoformat() if out['data_relatoriu'] else None,
				'data_akontesimentu': out['data_akontesimentu'].isoformat() if out['data_akontesimentu'] else None,
				'munisipiu': mun.pk if mun else None, 'postu': postu.pk if postu else None,
				'suku': suku.pk if suku else None, 'aldeia': aldeia.pk if aldeia else None,
				'latitude': str(lat) if lat is not None else None, 'longitude': str(lon) if lon is not None else None,
				'gps_aproksimadu': aproksimadu,
				'tipu_konflitu': [t.pk for t in tipu], 'tipu_seluk': _testu(d.get('tipu_seluk'))[:255],
				'tipu_rai': rai.pk if rai else None, 'deskrisaun': deskrisaun,
				'konsentimentu': konsentimentu, 'la_publika': _testu(d.get('la_publika')).upper() in SIN,
				'observasaun': _testu(d.get('observasaun')),
				**pop,
				'rbr': _kampu_extra(Kazu, KAMPU_KAZU_RBR, d, erru, avizu if at else None),
				'segimentu': _kampu_extra(KazuSegimentu, KAMPU_SEGIMENTU, d, erru, avizu if at else None),
				'referensia_rbr': ref, 'verifikadu': bool(d.get('_verifikadu')),
			},
			'rezumu': {
				'munisipiu': mun.name if mun else _testu(d.get('munisipiu')),
				'suku': suku.name if suku else '',
				'tipu': ', '.join(t.name for t in tipu),
				'deskrisaun': deskrisaun[:90], 'referensia': ref or '',
			},
		})
		rezultadu[-1]['ok'] = not erru                   # kampu RbR mós bele hatama erru
	return rezultadu


def kria_pratinjau(f, user):
	naran, sha, lina = lee_excel(f)
	rez = valida(lina)
	return KazuImport.objects.create(
		naran_file=naran, sha256=sha, dadus=rez, created_by=user, total=len(rez),
		total_ok=sum(1 for r in rez if r['ok']),
		total_aproksimadu=sum(1 for r in rez if r['ok'] and r['dadus']['gps_aproksimadu']))


# ══════════════ 3. Konfirma ══════════════
@transaction.atomic
def konfirma(imp, user):
	imp = KazuImport.objects.select_for_update().get(pk=imp.pk)
	if imp.status != KazuImport.RASCUNHO:
		raise ValidationError(_('Import ne\'e konfirma ka kansela ona.'))
	kria = 0
	for r in imp.dadus:
		if not r['ok']:
			continue
		d = r['dadus']
		verifikadu = d.get('verifikadu')                   # "Verified" iha Airtable → Verifikadu (hein Superadmin aprova)
		kazu = Kazu(
			titulu=d['titulu'], status=VERIFIED if verifikadu else SYNCED, synced_at=timezone.now(),
			referensia_rbr=d.get('referensia_rbr'),
			verified_by=user if verifikadu else None, verified_at=timezone.now() if verifikadu else None,
			data_relatoriu=date.fromisoformat(d['data_relatoriu']) if d['data_relatoriu'] else None,
			data_akontesimentu=date.fromisoformat(d['data_akontesimentu']) if d['data_akontesimentu'] else None,
			munisipiu_id=d['munisipiu'], postu_id=d['postu'], suku_id=d['suku'], aldeia_id=d['aldeia'],
			latitude=Decimal(d['latitude']), longitude=Decimal(d['longitude']), gps_aproksimadu=d['gps_aproksimadu'],
			tipu_seluk=d['tipu_seluk'], tipu_rai_id=d['tipu_rai'], deskrisaun=d['deskrisaun'],
			konsentimentu=d['konsentimentu'], la_publika=d['la_publika'], observasaun=d['observasaun'],
			created_by=user, importasaun=imp)
		for campo, v in d.get('rbr', {}).items():           # pergunta formuláriu RbR
			setattr(kazu, campo, Kazu._meta.get_field(campo).to_python(v))
		kazu.kode = generate_kode(kazu)
		kazu.save()
		kazu.tipu_konflitu.set(d['tipu_konflitu'])
		if any(d.get(c) is not None for c in ('uma_kain', 'mane', 'feto', 'labarik', 'total_ema', 'katuas_ferik', 'defisiensia')):
			total = d.get('total_ema') or ((d.get('mane') or 0) + (d.get('feto') or 0)) or None
			UmaKainAfetada.objects.create(kazu=kazu, uma_kain=d.get('uma_kain'), mane=d.get('mane'), feto=d.get('feto'),
				labarik=d.get('labarik'), total_ema=total, katuas_ferik=d.get('katuas_ferik'), defisiensia=d.get('defisiensia'))
		if d.get('segimentu'):                              # tribunál, notifikasaun, status (dadus tuan Airtable)
			KazuSegimentu.objects.create(kazu=kazu, updated_by=user, **{
				c: KazuSegimentu._meta.get_field(c).to_python(v) for c, v in d['segimentu'].items()})
		_historia(kazu, user, '', kazu.status, _('Import Excel: %(f)s · liña %(n)s') % {'f': imp.naran_file, 'n': r['lina']} +
			(f' · {kazu.referensia_rbr}' if kazu.referensia_rbr else ''))
		kria += 1
	imp.status = KazuImport.REMATA
	imp.konfirma_iha = timezone.now()
	imp.save(update_fields=['status', 'konfirma_iha'])
	if kria:
		msg = lambda: _('Admin import kazu %(n)s husi Excel (%(f)s). Hein verifikasaun no aprovasaun.') % {'n': kria, 'f': imp.naran_file}
		transaction.on_commit(lambda: kirim_notif_role([SUPERADMIN], 'KAZU_FOUN', msg, url='/kazu/', actor=user, email=False))
	return kria


# ══════════════ 4. Hadia lokasaun (mapa) ══════════════
def pode_muda_lokasaun(kazu):
	# Admin bele muda fatin molok kazu aprova (depois aprova, dadus fiksu)
	return kazu.status in (SYNCED, VERIFIED)


@transaction.atomic
def muda_lokasaun(kazu, user, lat, lon):
	if not (TL_LAT[0] <= lat <= TL_LAT[1] and TL_LON[0] <= lon <= TL_LON[1]):
		raise ValidationError(_('Koordenada GPS la iha territóriu Timor-Leste.'))
	antes = f'{kazu.latitude}, {kazu.longitude}'
	kazu.latitude, kazu.longitude, kazu.gps_aproksimadu = lat, lon, False
	kazu.save(update_fields=['latitude', 'longitude', 'gps_aproksimadu'])
	_historia(kazu, user, kazu.status, kazu.status, _('Lokasaun muda: %(a)s → %(b)s, %(c)s') % {'a': antes, 'b': lat, 'c': lon}, tipu=KazuHistoria.EDITA)
	return kazu
