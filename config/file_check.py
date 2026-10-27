"""Verifika file upload tuir KONTEÚDU (la fiar extensaun ka naran file).

Ema bele muda naran file ida (ex. script.php → foto.jpg). Tan ne'e:
  1. Deteta tipu loos husi bytes dahuluk (magic bytes), la'ós husi extensaun.
  2. Extensaun tenke hanesan ho konteúdu.
  3. Foto: Pillow descodifika imajen tomak (file falsu falla) — depois kompresa/re-enkoda
     (config.upload_utils.compress_image) atu hamoos kódigu ne'ebé subar iha imajen.
  4. PDF: rejeita JavaScript, Launch no file embutidu.
  5. DOCX / XLSX: tenke ZIP Office loos; rejeita makro (vbaProject.bin) no zip-bomba.
  6. Vídeo: kontentor MP4/MOV/3GP (ftyp) ka WebM (EBML).
Uza: tipu = valida_upload(f, {'jpg', 'png', 'pdf'}, max_mb=10)
"""
import io
import re
import zipfile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# extensaun naran file → tipu konteúdu
EXT_TIPU = {
	'jpg': 'jpg', 'jpeg': 'jpg', 'png': 'png', 'webp': 'webp', 'gif': 'gif',
	'pdf': 'pdf', 'docx': 'docx', 'xlsx': 'xlsx', 'csv': 'csv',
	'mp4': 'mp4', 'mov': 'mp4', '3gp': 'mp4', 'm4v': 'mp4', 'webm': 'webm',
}
IMAJEN = {'jpg', 'png', 'webp', 'gif'}
VIDEO = {'mp4', 'webm'}
PDF_PERIGU = re.compile(rb'/(JavaScript|JS|Launch|EmbeddedFiles?|RichMedia|XFA)\b')
ZIP_MAX_DESKOMPRIME = 200 * 1024 * 1024            # proteje kontra zip-bomba
TESTU_PERIGU = re.compile(rb'<\s*(script|html|iframe|object|embed|svg)\b|<\?php', re.I)


def _le(f, n=None):
	f.seek(0)
	d = f.read() if n is None else f.read(n)
	f.seek(0)
	return d


def deteta_tipu(f):
	"""Tipu loos husi konteúdu: jpg/png/webp/gif/pdf/docx/xlsx/mp4/webm, ka None."""
	h = _le(f, 32)
	if h.startswith(b'\xff\xd8\xff'):
		return 'jpg'
	if h.startswith(b'\x89PNG\r\n\x1a\n'):
		return 'png'
	if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
		return 'webp'
	if h[:6] in (b'GIF87a', b'GIF89a'):
		return 'gif'
	if h.startswith(b'%PDF-'):
		return 'pdf'
	if h[4:8] == b'ftyp':
		return 'mp4'
	if h.startswith(b'\x1a\x45\xdf\xa3'):
		return 'webm'
	if h.startswith(b'PK\x03\x04'):
		try:
			with zipfile.ZipFile(f) as z:
				naran = set(z.namelist())
		except zipfile.BadZipFile:
			return None
		finally:
			f.seek(0)
		if 'word/document.xml' in naran:
			return 'docx'
		if 'xl/workbook.xml' in naran:
			return 'xlsx'
	return None


def _valida_imajen(f):
	from PIL import Image
	try:
		img = Image.open(f)
		img.verify()                      # estrutura
		f.seek(0)
		img = Image.open(f)
		img.load()                        # descodifika pixel hotu
		if img.width < 1 or img.height < 1 or img.width * img.height > 80_000_000:
			raise ValueError
	except Exception:
		raise ValidationError(_('Imajen la validu ka estraga.'))
	finally:
		f.seek(0)
	# Imajen poliglota: imajen loos + kódigu (PHP/HTML/script) subar iha laran ka iha rohan
	if TESTU_PERIGU.search(_le(f)):
		raise ValidationError(_('Imajen iha kódigu subar. File la permite.'))


def _valida_pdf(f):
	dadus = _le(f)
	if b'%%EOF' not in dadus[-2048:]:
		raise ValidationError(_('PDF la kompletu ka estraga.'))
	if PDF_PERIGU.search(dadus):
		raise ValidationError(_('PDF iha JavaScript ka file subar. Ba seguransa, rai fali hanesan PDF simples (Print → PDF).'))


def _valida_office(f, tipu):
	try:
		with zipfile.ZipFile(f) as z:
			if z.testzip() is not None:
				raise ValidationError(_('File Office estraga.'))
			total = sum(i.file_size for i in z.infolist())
			naran = [i.filename.lower() for i in z.infolist()]
	except zipfile.BadZipFile:
		raise ValidationError(_('File Office estraga.'))
	finally:
		f.seek(0)
	if total > ZIP_MAX_DESKOMPRIME:
		raise ValidationError(_('File Office boot liu bainhira loke.'))
	if any(n.endswith('vbaproject.bin') or n.endswith('.exe') or n.endswith('.dll') for n in naran):
		raise ValidationError(_('File iha makro ka programa. Rai fali hanesan .%(ext)s simples.') % {'ext': tipu})


def _valida_csv(f):
	dadus = _le(f, 64 * 1024)
	if b'\x00' in dadus or TESTU_PERIGU.search(dadus):
		raise ValidationError(_('File CSV la validu.'))
	for kodigu in ('utf-8-sig', 'cp1252', 'latin-1'):
		try:
			dadus.decode(kodigu)
			return
		except UnicodeDecodeError:
			continue
	raise ValidationError(_('File CSV la validu.'))


def valida_upload(f, permite, max_mb=None):
	"""Valida file upload. `permite` = tipu konteúdu (ex. {'jpg','png','pdf'}). Retorna tipu loos.
	Muda naran file ba extensaun loos (ex. foto.PNG ne'ebé loloos JPEG → foto.jpg)."""
	naran = getattr(f, 'name', '') or ''
	ext = naran.rsplit('.', 1)[-1].lower() if '.' in naran else ''
	lista = ', '.join(sorted({e for e, t in EXT_TIPU.items() if t in permite}))
	if EXT_TIPU.get(ext) not in permite:
		raise ValidationError(_('Formatu file la permite (%(naran)s). Uza: %(ext)s') % {'naran': naran[-60:], 'ext': lista})
	if max_mb and f.size > max_mb * 1024 * 1024:
		raise ValidationError(_('File boot liu (%(naran)s). Máximu %(mb)s MB.') % {'naran': naran[-60:], 'mb': max_mb})
	if f.size == 0:
		raise ValidationError(_('File mamuk.'))
	tipu = 'csv' if EXT_TIPU.get(ext) == 'csv' else deteta_tipu(f)
	# Tipu loos tenke hanesan ho extensaun (imajen ho imajen: foto.png ne'ebé loloos JPEG bele)
	hanesan = tipu == EXT_TIPU[ext] or (tipu in IMAJEN and EXT_TIPU[ext] in IMAJEN)
	if tipu is None or tipu not in permite or not hanesan:
		raise ValidationError(_('Konteúdu file la hanesan ho extensaun (%(naran)s). File bele estraga ka falsu.') % {'naran': naran[-60:]})
	if tipu in IMAJEN:
		_valida_imajen(f)
	elif tipu == 'pdf':
		_valida_pdf(f)
	elif tipu in ('docx', 'xlsx'):
		_valida_office(f, tipu)
	elif tipu == 'csv':
		_valida_csv(f)
	# Naran ho extensaun loos (upload_to uza extensaun husi naran)
	if tipu in IMAJEN and EXT_TIPU[ext] != tipu:
		f.name = naran.rsplit('.', 1)[0] + '.' + tipu
	return tipu


def imajen_seguru(f, max_px=1600, quality=82):
	"""Valida + re-enkoda imajen ba JPEG foun (hamoos EXIF no kódigu subar). ValidationError se la bele."""
	from config.upload_utils import compress_image
	valida_upload(f, IMAJEN)
	novu = compress_image(f, max_px=max_px, quality=quality)
	if novu is None:
		raise ValidationError(_('Imajen la validu ka estraga.'))
	return novu


def header_seguru(response):
	"""Header ba file upload ne'ebé serve: browser labele adivinha tipu ka hala'o script (sandbox)."""
	response['X-Content-Type-Options'] = 'nosniff'
	# PDF: Chrome labele hatudu PDF iha sandbox → PDF uluk verifika ona (la iha JavaScript)
	if not response.get('Content-Type', '').startswith('application/pdf'):
		response['Content-Security-Policy'] = "default-src 'none'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline'; sandbox"
	return response
