# ══════════════════════════════════════════════════════════════
# SMKRE — WSGI ba PythonAnywhere
# Kopia konteúdu ne'e ba: Web → "WSGI configuration file"
# (/var/www/<username>_pythonanywhere_com_wsgi.py). Troka <username>.
# ══════════════════════════════════════════════════════════════
import os
import sys

PROJETU = '/home/<username>/SMKRE'
if PROJETU not in sys.path:
	sys.path.insert(0, PROJETU)

os.chdir(PROJETU)                                  # .env lee husi pasta projetu
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smkre.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402
application = get_wsgi_application()
