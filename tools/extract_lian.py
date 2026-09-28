"""
Ekstrai testu tradusaun (msgid) husi template no kódigu Python → locale/<lian>/LC_MESSAGES/django.po
La presiza gettext. Tradusaun ne'ebé iha ona la lakon (merge).
Uza:  python tools/extract_lian.py   depois   python manage.py compile_lian
"""
import re
from pathlib import Path
import polib

BASE = Path(__file__).resolve().parent.parent
LANGS = ['tet', 'pt', 'en', 'id']   # tet: testu fonte (bele edita Tetun iha tet/django.po)
SKIP = ('locale', 'staticfiles', 'media', 'node_modules', '.git')

TPL_TRANS = re.compile(r'{%\s*trans(?:late)?\s+"([^"]+)"')
TPL_TRANS1 = re.compile(r"{%\s*trans(?:late)?\s+'([^']+)'")
TPL_UNDERSCORE = re.compile(r'_\("([^"]+)"\)')
TPL_BLOCK = re.compile(r'{%\s*blocktrans(?:late)?(?P<args>[^%]*)%}(?P<one>.*?)(?:{%\s*plural\s*%}(?P<many>.*?))?{%\s*endblocktrans(?:late)?\s*%}', re.S)
PY_CALL = re.compile(r'''\b_\(\s*(?P<q>['"])(?P<s>(?:\\.|(?!(?P=q)).)*)(?P=q)\s*\)''')


def norm_block(text):
	return re.sub(r'{{\s*(\w+)[^}]*}}', r'%(\1)s', text).strip()


def _ok(s):
	# la'ós testu dinámiku (ezemplu f-string "{title}")
	return not ('{' in s and '%(' not in s)


def collect():
	singles, plurals = {}, {}
	for path in BASE.rglob('*'):
		if any(part in SKIP for part in path.parts) or not path.is_file():
			continue
		rel = str(path.relative_to(BASE))
		if path.suffix in ('.html', '.txt') or (path.suffix == '.js' and 'templates' in path.parts):
			src = path.read_text(encoding='utf-8')
			for rx in (TPL_TRANS, TPL_TRANS1, TPL_UNDERSCORE):
				for m in rx.finditer(src):
					# {% trans %} Django duplika "%" → "%%" iha msgid
					singles.setdefault(m.group(1).replace('%', '%%') if rx is not TPL_UNDERSCORE else m.group(1), rel)
			for m in TPL_BLOCK.finditer(src):
				one = norm_block(m.group('one'))
				if m.group('many'):
					plurals.setdefault(one, (norm_block(m.group('many')), rel))
				else:
					singles.setdefault(one, rel)
		elif path.suffix == '.py' and 'migrations' not in path.parts and path.name != 'extract_lian.py':
			src = path.read_text(encoding='utf-8')
			for m in PY_CALL.finditer(src):
				singles.setdefault(m.group('s').replace("\\'", "'").replace('\\"', '"'), rel)
			for rx in (TPL_TRANS, TPL_TRANS1):   # {% trans %} iha HTML crispy (forms.py)
				for m in rx.finditer(src):
					singles.setdefault(m.group(1), rel)
	return singles, plurals


def main():
	singles, plurals = collect()
	for lang in LANGS:
		po_path = BASE / 'locale' / lang / 'LC_MESSAGES' / 'django.po'
		po_path.parent.mkdir(parents=True, exist_ok=True)
		po = polib.pofile(str(po_path)) if po_path.exists() else polib.POFile()
		po.metadata = {'Content-Type': 'text/plain; charset=UTF-8', 'Language': lang,
			'Plural-Forms': 'nplurals=1; plural=0;' if lang == 'id' else 'nplurals=2; plural=(n != 1);'}
		have = {e.msgid for e in po}
		ident = lang == 'tet'   # Tetun: msgstr = msgid (ekipa bele hadia testu Tetun iha ne'e la muda kódigu)
		for s, rel in sorted(singles.items()):
			if s not in have and _ok(s):
				po.append(polib.POEntry(msgid=s, msgstr=s if ident else '', occurrences=[(rel, '')]))
		for one, (many, rel) in sorted(plurals.items()):
			if one not in have:
				po.append(polib.POEntry(msgid=one, msgid_plural=many, msgstr_plural={0: one if ident else '', 1: many if ident else ''}, occurrences=[(rel, '')]))
		po.save(str(po_path))
		print(f'{lang}: {len(po)} testu · {po.percent_translated()}% tradus')


if __name__ == '__main__':
	main()
