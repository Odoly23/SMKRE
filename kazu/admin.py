from django.contrib import admin
from kazu.models import Kazu, UmaKainAfetada, InsidenteEviksaun, AtorEnvolvidu, Evidensia, KazuHistoria, KazuSequence


class AfetaduInline(admin.TabularInline):
	model = UmaKainAfetada
	extra = 0


class InsidenteInline(admin.StackedInline):
	model = InsidenteEviksaun
	extra = 0


class AtorInline(admin.TabularInline):
	model = AtorEnvolvidu
	extra = 0


class EvidensiaInline(admin.TabularInline):
	model = Evidensia
	extra = 0
	readonly_fields = ['uploaded_by', 'uploaded_at']


class HistoriaInline(admin.TabularInline):
	model = KazuHistoria
	extra = 0
	can_delete = False
	readonly_fields = ['tipu', 'status_antes', 'status_foun', 'nota', 'user', 'created_at']


@admin.register(Kazu)
class KazuAdmin(admin.ModelAdmin):
	list_display = ['__str__', 'status', 'status_kazu', 'munisipiu', 'urjente', 'created_by', 'created_at']
	list_filter = ['status', 'status_kazu', 'urjente', 'munisipiu', 'tipu_konflitu']
	search_fields = ['kode', 'titulu', 'deskrisaun']
	readonly_fields = ['kode', 'synced_at', 'verified_by', 'verified_at', 'approved_by', 'approved_at', 'created_by']
	inlines = [AfetaduInline, InsidenteInline, AtorInline, EvidensiaInline, HistoriaInline]


admin.site.register(KazuSequence)
