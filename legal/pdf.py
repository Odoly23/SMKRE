"""PDF husi template HTML (xhtml2pdf, Python puru — la presiza programa sistema). Kop surat Rede ba Rai."""
import io
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string

# Kop surat ofisiál Rede ba Rai (husi dokumentu "Perguntas Xave Sira Legal")
KOP = {
	'naran': 'Rede ba Rai',
	'linha': [
		'Sekretariadu Kdadalak Sulimutuk Institut.',
		'Edifisiu: Fundasaun Haburas. Rua dos direitus humanos no. 16, Aldeia Halibur,',
		'Suco Motael, Posto Administrativo Verra Cruz, Munisipiu Dili, Timor Leste.',
		'Website:www.redeberai.org, Email:redebarai@gmail.com',
		'Telemovel +670-77444414, 77542969, 77811481',
	],
}


def _link_callback(files):
	# xhtml2pdf presiza dalan file lokál: "static:..." → static finder, "file:<id>" → file survei (protejidu)
	def cb(uri, rel):
		if uri.startswith('static:'):
			return finders.find(uri[7:]) or ''
		if uri.startswith('file:'):
			f = files.get(uri[5:])
			return f.file.path if f else ''
		return ''
	return cb


def render_pdf(template, context, naran, files=None):
	from xhtml2pdf import pisa
	html = render_to_string(template, dict(context, kop=KOP))
	out = io.BytesIO()
	res = pisa.CreatePDF(html, dest=out, encoding='utf-8', link_callback=_link_callback(files or {}))
	if res.err:
		raise RuntimeError('PDF la bele kria')
	response = HttpResponse(out.getvalue(), content_type='application/pdf')
	response['Content-Disposition'] = f'inline; filename="{naran}.pdf"'
	response['Cache-Control'] = 'private, no-store'
	return response
