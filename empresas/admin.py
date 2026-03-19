from django.contrib import admin
from django.utils.html import format_html

from .models import Contacto, Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'razon_social', 'tipo_inmueble', 'created_at']
    search_fields = ['nombre', 'razon_social']
    readonly_fields = ['created_at', 'logo_preview']
    fields = ['nombre', 'razon_social', 'tipo_inmueble', 'logo', 'logo_preview', 'created_at']

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="80" />', obj.logo.url)
        return format_html('<span>-</span>')
    logo_preview.short_description = 'Vista previa del logo'


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cargo', 'empresa', 'telefono_principal')
    list_filter = ('empresa',)
    search_fields = ('nombre', 'cargo', 'correo_principal', 'telefono_principal')
    autocomplete_fields = ('empresa',)
