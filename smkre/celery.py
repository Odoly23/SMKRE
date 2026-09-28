import os
from celery import Celery

# Celery: knaar kotuk (email, kompresa vídeo, eksporta relatóriu, knaar horáriu)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smkre.settings')

app = Celery('smkre')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
