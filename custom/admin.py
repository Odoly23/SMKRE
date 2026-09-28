from django.contrib import admin
from custom.models import Munisipiu, PostuAdministrativu, Suku, Aldeia, Pozisaun, \
	TipuKonflitu, TipuRai, TipuEviksaun, TipuAtor, EstraguPatrimoniu, NesesidadeUrjente


@admin.register(Munisipiu)
class MunisipiuAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'latitude', 'longitude', 'is_active']
	search_fields = ['code', 'name']


@admin.register(PostuAdministrativu)
class PostuAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'munisipiu', 'is_active']
	list_filter = ['munisipiu']
	search_fields = ['code', 'name']


@admin.register(Suku)
class SukuAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'postu', 'is_active']
	list_filter = ['postu__munisipiu']
	search_fields = ['code', 'name']
	autocomplete_fields = ['postu']


@admin.register(Aldeia)
class AldeiaAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'suku', 'is_active']
	list_filter = ['suku__postu__munisipiu']
	search_fields = ['code', 'name']
	autocomplete_fields = ['suku']


@admin.register(Pozisaun, TipuKonflitu, TipuRai, TipuEviksaun, TipuAtor, EstraguPatrimoniu, NesesidadeUrjente)
class OpsaunAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'order', 'is_active']
	list_editable = ['order', 'is_active']
	search_fields = ['code', 'name']
