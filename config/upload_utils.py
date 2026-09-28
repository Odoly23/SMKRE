import io
import logging
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps

logger = logging.getLogger('smkre')
FOTO_MAX_PX = 1600
FOTO_QUALITY = 80


def compress_image(f, max_px=FOTO_MAX_PX, quality=FOTO_QUALITY):
	# Kompresa foto ba ~1 MB (JPEG, maximu 1600px) no hamoos metadata EXIF (privasidade)
	try:
		img = Image.open(f)
		img = ImageOps.exif_transpose(img)
		if img.mode not in ('RGB', 'L'):
			img = img.convert('RGB')
		img.thumbnail((max_px, max_px), Image.LANCZOS)
		out = io.BytesIO()
		img.save(out, format='JPEG', quality=quality, optimize=True)
		out.seek(0)
		name = f.name.rsplit('.', 1)[0] + '.jpg'
		return InMemoryUploadedFile(out, 'file', name, 'image/jpeg', out.getbuffer().nbytes, None)
	except Exception as e:
		logger.error(f'Foto la bele kompresa: {e}')
		return None
