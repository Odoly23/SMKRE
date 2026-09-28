from django.contrib import admin
from publiku.models import Publikasaun


@admin.register(Publikasaun)
class PublikasaunAdmin(admin.ModelAdmin):
	list_display = ['titulu', 'tipu', 'lian', 'data', 'status', 'created_by']
	list_filter = ['status', 'tipu', 'lian']
