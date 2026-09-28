from django.contrib import admin
from notification.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ['recipient', 'tipu', 'message', 'is_urgent', 'is_read', 'created_at']
	list_filter = ['tipu', 'is_urgent', 'is_read']
	search_fields = ['recipient__username', 'message']
