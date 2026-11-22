"""Entrada aplikasaun ba cPanel "Setup Python App" (Phusion Passenger).
cPanel: Application startup file = passenger_wsgi.py · Application Entry point = application"""
import os
import sys

# pasta projetu iha sys.path (Passenger hahú husi pasta seluk)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smkre.settings')

from smkre.wsgi import application  # noqa: E402,F401
