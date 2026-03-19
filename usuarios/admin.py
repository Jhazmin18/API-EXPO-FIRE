"""
Configuración del admin para usuarios.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = [
        'get_username',
        'get_nombre_completo',
        'empresa',
        'telefono',
        'domicilio',
        'get_foto_preview',
        'rol',
        'created_at',
        'updated_at',
    ]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'empresa__nombre']
    fields = ['user', 'empresa', 'telefono', 'domicilio', 'rol', 'foto_perfil', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Usuario')
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description='Nombre completo')
    def get_nombre_completo(self, obj):
        return obj.nombre_completo

    @admin.display(description='Foto')
    def get_foto_preview(self, obj):
        if obj.foto_perfil:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 50%;" />',
                obj.foto_perfil.url
            )
        return '-'
