from django.contrib import admin
from users.models import Pesoal, PesoalUser, OfflinePermission


class PesoalUserInline(admin.StackedInline):
	model = PesoalUser
	extra = 0
	can_delete = False


@admin.register(Pesoal)
class PesoalAdmin(admin.ModelAdmin):
	list_display = ['name', 'email', 'sexo', 'pos', 'munisipiu', 'phone']
	list_filter = ['sexo', 'munisipiu', 'pos']
	search_fields = ['name', 'email', 'phone']
	inlines = [PesoalUserInline]


@admin.register(OfflinePermission)
class OfflinePermissionAdmin(admin.ModelAdmin):
	list_display = ['user', 'given_by', 'start_date', 'end_date', 'is_active']
	list_filter = ['is_active']
	search_fields = ['user__username', 'user__email']
	readonly_fields = ['cancelled_by', 'cancelled_at']
