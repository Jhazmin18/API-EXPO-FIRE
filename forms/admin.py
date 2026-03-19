from django.contrib import admin

from .models import (
    FormTemplate,
    Question,
    QuestionOption,
    FormRun,
)


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'version', 'activo', 'creado_en')
    list_filter = ('codigo', 'activo')
    search_fields = ('codigo', 'titulo')
    filter_horizontal = ('empresas_permitidas',)
    fields = (
        'codigo',
        'titulo',
        'version',
        'activo',
        'descripcion',
        'header_requiere_en_establecimiento',
        'roles_permitidos',
        'empresas_permitidas',
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('clave', 'template', 'tipo', 'requerido', 'orden')
    list_filter = ('template__codigo', 'tipo', 'requerido')
    search_fields = ('clave', 'etiqueta')
    autocomplete_fields = ('template',)


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('pregunta', 'valor', 'etiqueta')
    list_filter = ('pregunta__template__codigo',)
    search_fields = ('valor', 'etiqueta')
    autocomplete_fields = ('pregunta',)


@admin.register(FormRun)
class FormRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'empresa', 'tecnico', 'estado', 'scope_type', 'scope_id', 'tiene_incidencias')
    list_filter = ('estado', 'scope_type', 'tiene_incidencias', 'template__codigo')
    search_fields = ('scope_id',)
    autocomplete_fields = ('template', 'empresa', 'tecnico')
