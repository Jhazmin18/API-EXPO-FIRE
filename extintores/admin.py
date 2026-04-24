"""
Configuración del Django Admin para la gestión de extintores.

Este módulo personaliza la interfaz de administración de Django
para facilitar la gestión de extintores.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Extintor

@admin.register(Extintor)
class ExtintorAdmin(admin.ModelAdmin):
    """
    Configuración personalizada del admin para el modelo Extintor.
    
    Incluye:
    - Vista de lista con campos principales y estado
    - Filtros por tipo, ubicación y fechas
    - Búsqueda por código y ubicación
    - Vista previa del QR code en la lista
    - Campos readonly para timestamps y QR
    """
    
    # Configuración de la lista
    list_display = [
        'codigo',
        'ubicacion',
        'empresa',
        'tipo',
        'modalidad',
        'capacidad',
        'get_estado_display',
        'fecha_vencimiento',
        'proxima_revision',
        'get_qr_preview',
    ]

    list_filter = [
        'empresa',
        'tipo',
        'modalidad',
        'fecha_vencimiento',
        'proxima_revision',
        'created_at',
    ]
    
    search_fields = [
        'codigo',
        'ubicacion',
        'observaciones',
    ]
    
    # Campos readonly
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'get_estado_display',
        'get_dias_vencimiento',
        'get_dias_revision',
        'get_qr_image',
    ]
    
    # Organización del formulario
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'id',
                'codigo',
                'empresa',
                'ubicacion',
                'tipo',
                'modalidad',
                'clase_fuego',
                'capacidad',
            )
        }),
        ('Fechas Importantes', {
            'fields': (
                'fecha_fabricacion',
                'fecha_vencimiento',
                'ultima_revision',
                'proxima_revision',
            )
        }),
        ('Estado Actual', {
            'fields': (
                'get_estado_display',
                'get_dias_vencimiento',
                'get_dias_revision',
            )
        }),
        ('Código QR', {
            'fields': (
                'get_qr_image',
                'qr_code',
            )
        }),
        ('Información Adicional', {
            'fields': (
                'observaciones',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Ordenamiento por defecto
    ordering = ['-created_at']
    
    # Número de elementos por página
    list_per_page = 25
    
    # Métodos personalizados para el admin
    
    @admin.display(description='Estado', ordering='fecha_vencimiento')
    def get_estado_display(self, obj):
        """
        Muestra el estado del extintor con colores.
        """
        # Si el objeto no tiene ID aún (es nuevo), no mostrar estado
        if not obj.id:
            return '-'
        
        estado = obj.estado
        colores = {
            'verde': '#28a745',
            'amarillo': '#ffc107',
            'rojo': '#dc3545',
        }
        
        iconos = {
            'verde': '✓',
            'amarillo': '⚠',
            'rojo': '✗',
        }
        
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 16px;">{} {}</span>',
            colores[estado],
            iconos[estado],
            estado.upper()
        )
    
    @admin.display(description='QR Preview')
    def get_qr_preview(self, obj):
        """
        Muestra una miniatura del QR en la lista.
        """
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="40" height="40" />',
                obj.qr_code.url
            )
        return '-'
    
    @admin.display(description='Código QR')
    def get_qr_image(self, obj):
        """
        Muestra el QR code completo en el detalle.
        """
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="300" height="300" style="image-rendering: pixelated;" />',
                obj.qr_code.url
            )
        return 'No generado'
    
    @admin.display(description='Días para vencer')
    def get_dias_vencimiento(self, obj):
        """
        Muestra los días restantes para el vencimiento.
        """
        dias = obj.dias_para_vencer
        if dias is None:
            return '-'
        if dias < 0:
            return format_html('<span style="color: red; font-weight: bold;">Vencido hace {} días</span>', abs(dias))
        elif dias <= 30:
            return format_html('<span style="color: red; font-weight: bold;">{} días</span>', dias)
        elif dias <= 60:
            return format_html('<span style="color: orange; font-weight: bold;">{} días</span>', dias)
        else:
            return format_html('<span style="color: green;">{} días</span>', dias)
    
    @admin.display(description='Días para revisión')
    def get_dias_revision(self, obj):
        """
        Muestra los días restantes para la próxima revisión.
        """
        dias = obj.dias_para_revision
        if dias is None:
            return '-'
        if dias < 0:
            return format_html('<span style="color: red; font-weight: bold;">Vencida hace {} días</span>', abs(dias))
        elif dias <= 15:
            return format_html('<span style="color: red; font-weight: bold;">{} días</span>', dias)
        elif dias <= 30:
            return format_html('<span style="color: orange; font-weight: bold;">{} días</span>', dias)
        else:
            return format_html('<span style="color: green;">{} días</span>', dias)
    
    def save_model(self, request, obj, form, change):
        """
        Sobrescribe el guardado para regenerar el QR si es necesario.
        """
        # Si es una actualización y el código cambió, regenerar QR
        if change and 'codigo' in form.changed_data:
            obj.qr_code = None  # Forzar regeneración
        
        super().save_model(request, obj, form, change)


# Personalización del sitio de administración
admin.site.site_header = "Sistema de Gestión de Extintores"
admin.site.site_title = "Gestión de Extintores"
admin.site.index_title = "Panel de Administración"


