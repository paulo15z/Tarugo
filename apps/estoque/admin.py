from django.contrib import admin
from .models import MaterialType, Location, MDFSheet, CutOff

@admin.register(MaterialType)
class MaterialTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(MDFSheet)
class MDFSheetAdmin(admin.ModelAdmin):
    list_display = ('material_type', 'width', 'height', 'thickness', 'quantity', 'location', 'entry_date')
    list_filter = ('material_type', 'location', 'thickness')
    search_fields = ('material_type__name', 'notes')
    date_hierarchy = 'entry_date'

@admin.register(CutOff)
class CutOffAdmin(admin.ModelAdmin):
    list_display = ('material_type', 'width', 'height', 'thickness', 'quantity', 'location', 'origin_sheet', 'entry_date')
    list_filter = ('material_type', 'location', 'thickness')
    search_fields = ('material_type__name', 'notes')
    date_hierarchy = 'entry_date'
