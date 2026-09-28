from django.contrib import admin
from legal.models import DokumentuLegal, NotaLegal, AsesuVault


@admin.register(DokumentuLegal)
class DokumentuLegalAdmin(admin.ModelAdmin):
	list_display = ['titulu', 'kategoria', 'kazu', 'versaun', 'atual', 'arkivadu', 'konfidensial', 'uploaded_at']
	list_filter = ['kategoria', 'atual', 'arkivadu', 'konfidensial']
	search_fields = ['titulu', 'kazu__kode', 'sha256']
	readonly_fields = ['sha256', 'tamanu', 'naran_orijinal', 'versaun', 'versaun_anterior', 'uploaded_by', 'uploaded_at']


@admin.register(NotaLegal)
class NotaLegalAdmin(admin.ModelAdmin):
	list_display = ['kazu', 'tipu', 'prazu', 'remata', 'created_by', 'created_at']
	list_filter = ['tipu', 'remata']


@admin.register(AsesuVault)
class AsesuVaultAdmin(admin.ModelAdmin):
	# Auditoria: lee deit (labele muda ka hamoos)
	list_display = ['at', 'aksaun', 'dokumentu', 'user', 'ip']
	list_filter = ['aksaun']
	search_fields = ['dokumentu__titulu', 'user__username', 'ip']

	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False
