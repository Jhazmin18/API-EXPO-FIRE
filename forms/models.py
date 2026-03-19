from django.db import models
from django.conf import settings

from empresas.models import Empresa


class FormTemplate(models.Model):
    codigo = models.CharField('Código', max_length=50, db_index=True)
    titulo = models.CharField('Título', max_length=150)
    version = models.PositiveIntegerField('Versión')
    activo = models.BooleanField('Activo', default=False)
    descripcion = models.TextField('Descripción', blank=True, null=True)
    header_requiere_en_establecimiento = models.BooleanField(
        'Header: requiere pregunta en establecimiento',
        default=False,
        help_text=(
            'Si está activo, el frontend debe preguntar si se encuentra en el '
            'establecimiento y, cuando responda "no", pedir referencia abierta.'
        ),
    )
    roles_permitidos = models.JSONField(
        'Roles permitidos',
        default=list,
        blank=True,
        help_text='Lista de roles con acceso. Vacío = todos los roles.',
    )
    empresas_permitidas = models.ManyToManyField(
        Empresa,
        blank=True,
        related_name='templates_formulario_permitidos',
        verbose_name='Empresas permitidas',
        help_text='Empresas con acceso. Vacío = todas las empresas.',
    )
    creado_en = models.DateTimeField('Creado en', auto_now_add=True)
    actualizado_en = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'forms_form_template'
        unique_together = ('codigo', 'version')
        verbose_name = 'Plantilla de formulario'
        verbose_name_plural = 'Plantillas de formularios'
        ordering = ['codigo', '-version']

    def __str__(self):
        return f"{self.codigo} v{self.version}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.activo:
            FormTemplate.objects.filter(codigo=self.codigo).exclude(pk=self.pk).update(activo=False)

    def is_available_for(self, user, empresa_id=None):
        if not user or not user.is_authenticated:
            return False

        if not self.activo:
            return False

        perfil = getattr(user, 'perfil', None)
        user_role = getattr(perfil, 'rol', None)
        user_empresa_id = getattr(perfil, 'empresa_id', None)
        resolved_empresa_id = empresa_id or user_empresa_id

        roles = self.roles_permitidos or []
        if roles and user_role not in roles:
            return False

        if self.empresas_permitidas.exists():
            if not resolved_empresa_id:
                return False
            if not self.empresas_permitidas.filter(id=resolved_empresa_id).exists():
                return False

        return True


class Question(models.Model):
    TIPO_BOOLEANO = 'booleano'
    TIPO_TEXTO = 'texto'
    TIPO_NUMERO = 'numero'
    TIPO_SELECCION = 'seleccion'
    TIPO_MULTI = 'multiseleccion'
    TIPO_FECHA = 'fecha'
    TIPO_ARCHIVO = 'archivo'

    TIPO_CHOICES = [
        (TIPO_BOOLEANO, 'Booleano'),
        (TIPO_TEXTO, 'Texto'),
        (TIPO_NUMERO, 'Número'),
        (TIPO_SELECCION, 'Selección'),
        (TIPO_MULTI, 'Multiselección'),
        (TIPO_FECHA, 'Fecha'),
        (TIPO_ARCHIVO, 'Archivo'),
    ]

    template = models.ForeignKey(
        FormTemplate,
        on_delete=models.CASCADE,
        related_name='preguntas',
        verbose_name='Plantilla',
    )
    clave = models.CharField('Clave', max_length=64)
    etiqueta = models.CharField('Etiqueta', max_length=255)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    requerido = models.BooleanField('Requerido', default=False)
    orden = models.PositiveIntegerField('Orden', default=0)
    ayuda = models.TextField('Ayuda', blank=True, null=True)
    reglas_visibilidad = models.JSONField('Reglas de visibilidad', blank=True, null=True, default=dict)
    reglas_validacion = models.JSONField('Reglas de validación', blank=True, null=True, default=dict)

    class Meta:
        db_table = 'forms_question'
        unique_together = ('template', 'clave')
        ordering = ['orden']

    def __str__(self):
        return f"{self.template.codigo} - {self.clave}"


class QuestionOption(models.Model):
    pregunta = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='opciones',
        verbose_name='Pregunta',
    )
    valor = models.CharField('Valor', max_length=100)
    etiqueta = models.CharField('Etiqueta', max_length=255)
    orden = models.PositiveIntegerField('Orden', default=0)

    class Meta:
        db_table = 'forms_question_option'
        unique_together = ('pregunta', 'valor')
        ordering = ['orden']

    def __str__(self):
        return f"{self.pregunta.clave} -> {self.valor}"


class FormRun(models.Model):
    ESTADO_BORRADOR = 'borrador'
    ESTADO_COMPLETADO = 'completado'
    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_COMPLETADO, 'Completado'),
    ]

    SCOPE_EXTINTOR = 'extintor'
    SCOPE_AREA = 'area'
    SCOPE_SITE = 'site'
    SCOPE_CHOICES = [
        (SCOPE_EXTINTOR, 'Extintor'),
        (SCOPE_AREA, 'Área'),
        (SCOPE_SITE, 'Sitio'),
    ]

    TIPO_LEVANTAMIENTO = 'levantamiento'
    TIPO_MANTENIMIENTO = 'mantenimiento'
    TIPO_RECARGA = 'recarga'
    TIPO_VENTA = 'venta'
    TIPO_INSPECCION = 'inspeccion'
    TIPO_SERVICIO_CHOICES = [
        (TIPO_LEVANTAMIENTO, 'Levantamiento'),
        (TIPO_MANTENIMIENTO, 'Mantenimiento'),
        (TIPO_RECARGA, 'Recarga'),
        (TIPO_VENTA, 'Venta'),
        (TIPO_INSPECCION, 'Inspección'),
    ]

    template = models.ForeignKey(
        FormTemplate,
        on_delete=models.PROTECT,
        related_name='ejecuciones',
        verbose_name='Plantilla'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='formularios',
        verbose_name='Empresa'
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='formularios',
        verbose_name='Técnico'
    )
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default=ESTADO_BORRADOR)
    scope_type = models.CharField('Scope type', max_length=20, choices=SCOPE_CHOICES)
    scope_id = models.CharField('Scope ID', max_length=64, db_index=True)
    tipo_servicio = models.CharField(
        'Tipo de servicio',
        max_length=30,
        choices=TIPO_SERVICIO_CHOICES,
        blank=True,
        null=True,
    )
    respuestas_json = models.JSONField('Respuestas', default=dict, blank=True)
    tiene_incidencias = models.BooleanField('Tiene incidencias', default=False)
    creado_en = models.DateTimeField('Creado en', auto_now_add=True)
    actualizado_en = models.DateTimeField('Actualizado en', auto_now=True)

    class Meta:
        db_table = 'forms_form_run'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['scope_type', 'scope_id']),
            models.Index(fields=['template']),
            models.Index(fields=['empresa']),
            models.Index(fields=['estado']),
            models.Index(fields=['tiene_incidencias']),
            models.Index(fields=['tipo_servicio']),
        ]

    def __str__(self):
        return f"{self.template.codigo} - {self.estado} ({self.id})"
