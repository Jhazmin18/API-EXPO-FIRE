# models.py (app extintores)
"""
Modelos de la aplicación de gestión de extintores

Este módulo define el modelo Extintor que representa un extintor
en el sistema de gestión.
"""
import os
import uuid
import calendar
import segno
from io import BytesIO
from urllib.parse import urlencode
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.functional import cached_property
from django.utils import timezone
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont

from empresas.models import Empresa


def qr_code_upload_to(instance, _filename):
    """
    Organiza el QR por empresa y usa un nombre único por archivo para evitar
    colisiones y problemas de caché al regenerar la imagen.
    """
    empresa_id = getattr(instance, 'empresa_id', None)
    empresa_folder = f'empresa_{empresa_id}' if empresa_id else 'empresa_sin_asignar'
    unique_id = uuid.uuid4().hex
    return f'empresas/{empresa_folder}/qr_codes/qr_{unique_id}.png'


def _load_font(size, bold=False):
    """
    Carga una fuente disponible tanto en Windows como en Linux/Railway.
    """
    candidates = [
        'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
        'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf',
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    for font_path in candidates:
        if not font_path:
            continue
        try:
            if os.path.isabs(font_path) and not os.path.exists(font_path):
                continue
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue
    return ImageFont.load_default()


class Extintor(models.Model):
    """
    Modelo que representa un extintor en el sistema.
    
    Attributes:
        id: UUID único para cada extintor
        codigo: Código único identificador del extintor
        ubicacion: Ubicación física del extintor
        tipo: Tipo de extintor según el agente extintor
        capacidad: Capacidad del extintor
        fecha_fabricacion: Fecha de fabricación del extintor
        fecha_vencimiento: Fecha de vencimiento del extintor
        ultima_revision: Fecha de la última revisión técnica
        proxima_revision: Fecha programada para la próxima revisión
        observaciones: Notas adicionales sobre el extintor
        qr_code: Imagen del código QR generado
        created_at: Fecha de creación del registro
        updated_at: Fecha de última actualización del registro
    """
    
    AGENTE_CHOICES = [
        ('PQS_ABC', 'Polvo químico seco ABC'),
        ('CO2', 'CO2'),
        ('AGUA', 'Agua'),
        ('ESPUMA', 'Espuma'),
        ('ACETATO_K', 'Acetato de potasio'),
        ('COLD_FIRE', 'Cold Fire'),
        ('CLASE_D', 'Clase D - cloruro de sodio'),
    ]

    MODALIDAD_CHOICES = [
        ('portatil', 'Portátil'),
        ('movil', 'Móvil'),
    ]
    
    # Campos principales
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )
    
    codigo = models.CharField(
        max_length=50,
        verbose_name='Código',
        help_text='Código único del extintor (ej: EXT-001)'
    )
    
    ubicacion = models.CharField(
        max_length=200,
        verbose_name='Ubicación',
        help_text='Ubicación física del extintor'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=AGENTE_CHOICES,
        default='PQS_ABC',
        verbose_name='Agente Extintor'
    )

    modalidad = models.CharField(
        max_length=20,
        choices=MODALIDAD_CHOICES,
        null=True,
        blank=True,
        verbose_name='Modalidad'
    )

    clase_fuego = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Clase de fuego',
        help_text='Clases de fuego que apaga el agente, separadas por coma. Ej: A,B,C'
    )
    
    capacidad = models.CharField(
        max_length=50,
        verbose_name='Capacidad',
        help_text='Capacidad del extintor (ej: 10 kg, 6 L)'
    )
    
    # Campos de fechas
    fecha_fabricacion = models.DateField(
        verbose_name='Fecha de Fabricación',
        null=True,
        blank=True
    )
    
    fecha_vencimiento = models.DateField(
        verbose_name='Fecha de Vencimiento',
        help_text='Fecha de vencimiento del extintor'
    )
    
    fecha_prueba_hidrostatica = models.DateField(
        verbose_name='Fecha de prueba hidrostatica',
        help_text='Fecha de prueba hidrostatica',
        null=True,
    )
    
    ultima_revision = models.DateField(
        verbose_name='Última Revisión',
        null=True,
        blank=True,
        help_text='Fecha de la última revisión técnica'
    )
    
    proxima_revision = models.DateField(
        verbose_name='Próxima Revisión',
        help_text='Fecha programada para la próxima revisión'
    )
    
    # Campos adicionales
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Notas adicionales sobre el extintor'
    )
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='extintores',
        verbose_name='Empresa',
        null=True,
        blank=True,
    )

    qr_code = models.ImageField(
        upload_to=qr_code_upload_to,
        blank=True,
        null=True,
        verbose_name='Código QR'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )

    arena = models.CharField(
        max_length=255,
        verbose_name='Arena contra incendios',
        blank=True,
        null=True,
    )
    
    # --- NUEVO CAMPO: Relación con el usuario que creó el extintor ---
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='extintores_creados',
        verbose_name='Creado por',
        help_text='Usuario que registró el extintor'
    )
    
    class Meta:
        verbose_name = 'Extintor'
        verbose_name_plural = 'Extintores'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'codigo'],
                name='unique_extintor_codigo_por_empresa',
            ),
        ]
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['ubicacion']),
            models.Index(fields=['fecha_vencimiento']),
        ]
    
    QR_BASE_URL = getattr(settings, 'FRONTEND_QR_BASE', 'http://localhost:5173/qr/')

    def __str__(self):
        return f"{self.codigo} - {self.ubicacion}"
    
    @property
    def estado(self):
        """
        Calcula el estado del extintor basado en fechas.
        
        Returns:
            str: 'verde', 'amarillo', o 'rojo'
        
        Lógica:
            - VERDE: Más de 60 días para vencer y próxima revisión a más de 30 días
            - AMARILLO: Entre 30-60 días para vencer o próxima revisión entre 15-30 días
            - ROJO: Menos de 30 días para vencer, vencido, o revisión vencida
        """
        # Validar que las fechas existan
        if not self.fecha_vencimiento or not self.proxima_revision:
            return 'rojo'  # Sin fechas = estado crítico
        
        hoy = timezone.now().date()
        
        # Verificar vencimiento
        dias_para_vencer = (self.fecha_vencimiento - hoy).days
        
        # Verificar próxima revisión
        dias_para_revision = (self.proxima_revision - hoy).days
        
        # Estado ROJO: Vencido o próximo a vencer (menos de 30 días)
        if dias_para_vencer < 0 or dias_para_revision < 0:
            return 'rojo'
        
        if dias_para_vencer <= 30 or dias_para_revision <= 15:
            return 'rojo'
        
        # Estado AMARILLO: Advertencia (30-60 días para vencer)
        if dias_para_vencer <= 60 or dias_para_revision <= 30:
            return 'amarillo'
        
        # Estado VERDE: Todo en orden
        return 'verde'
    
    @property
    def dias_para_vencer(self):
        """Calcula los días restantes hasta el vencimiento."""
        if not self.fecha_vencimiento:
            return None
        hoy = timezone.now().date()
        return (self.fecha_vencimiento - hoy).days
    
    @property
    def dias_para_revision(self):
        """Calcula los días restantes hasta la próxima revisión."""
        if not self.proxima_revision:
            return None
        hoy = timezone.now().date()
        return (self.proxima_revision - hoy).days
    
    @cached_property
    def estado_label(self):
        return self.estado.upper()

    def get_qr_url(self):
        base_url = self.QR_BASE_URL.rstrip('/')
        return f"{base_url}/{self.id}"

    def _build_label_image(self):
        # Etiqueta horizontal para cinta Brady M21 de 3/4" (19 mm).
        scale = 1.0
        label_width = 620
        label_height = 224
        margin = 12
        gap = 14
        qr_padding = 4

        qr = segno.make(self.get_qr_url(), error='h')
        qr_buffer = BytesIO()
        qr.save(qr_buffer, kind='png', scale=7, border=4, dark='#000000', light='white')
        qr_buffer.seek(0)
        qr_img = Image.open(qr_buffer).convert('RGB')

        # Hacemos el QR un poco más compacto para darle más protagonismo al texto.
        qr_size = int(label_height * 0.62)
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS
        qr_img = qr_img.resize((qr_size, qr_size), resample_filter)

        combined = Image.new('RGB', (label_width, label_height), 'white')
        qr_y = max(margin, (label_height - qr_size) // 2)
        combined.paste(qr_img, (margin, qr_y))

        draw = ImageDraw.Draw(combined)
        title_font = _load_font(72, bold=True)
        text_font = _load_font(54, bold=False)
        small_font = _load_font(40, bold=False)

        text_x = margin + qr_size + gap + qr_padding
        text_width = label_width - text_x - margin
        y = qr_y

        def truncate_text(text, font, max_width):
            text = str(text or '')
            if draw.textlength(text, font=font) <= max_width:
                return text
            ellipsis = '...'
            while text and draw.textlength(f'{text}{ellipsis}', font=font) > max_width:
                text = text[:-1]
            return f'{text}{ellipsis}' if text else ellipsis

        draw.text(
            (text_x, y),
            truncate_text(self.codigo, title_font, text_width),
            fill='#102347',
            font=title_font,
        )

        title_bbox = draw.textbbox((0, 0), 'Ag', font=title_font)
        y += (title_bbox[3] - title_bbox[1]) + 10
        draw.text(
            (text_x, y),
            truncate_text(self.get_tipo_display(), text_font, text_width),
            fill='#333333',
            font=text_font,
        )

        text_bbox = draw.textbbox((0, 0), 'Ag', font=text_font)
        y += (text_bbox[3] - text_bbox[1]) + 8
        draw.text(
            (text_x, y),
            truncate_text(f'Ubicacion: {self.ubicacion}', small_font, text_width),
            fill='#555555',
            font=small_font,
        )

        small_bbox = draw.textbbox((0, 0), 'Ag', font=small_font)
        y += (small_bbox[3] - small_bbox[1]) + 6
        draw.text(
            (text_x, y),
            truncate_text(f'Capacidad: {self.capacidad}', small_font, text_width),
            fill='#555555',
            font=small_font,
        )

        fecha_venc = self.fecha_vencimiento.strftime('%Y-%m-%d') if self.fecha_vencimiento else 'Sin fecha'
        y += (small_bbox[3] - small_bbox[1]) + 6
        draw.text(
            (text_x, y),
            truncate_text(f'Vence: {fecha_venc}', small_font, text_width),
            fill='#555555',
            font=small_font,
        )
        return combined

    def obtener_etiqueta_png(self):
        combined = self._build_label_image()
        buffer = BytesIO()
        combined.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    def generar_qr(self):
        """
        Genera el código QR para el extintor.

        El QR contiene la URL para acceder a la información del extintor.
        Se guarda automáticamente en el campo qr_code.
        """
        combined = self._build_label_image()

        # Guardar en un buffer
        buffer = BytesIO()
        combined.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Guardar en el modelo
        filename = f'qr_{self.id.hex}.png'
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        buffer.close()

    def regenerar_qr(self):
        """
        Fuerza la regeneración del QR usando la URL actual.
        """
        if self.qr_code:
            self.qr_code.delete(save=False)
            self.qr_code = None
        self.save()
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar el QR automáticamente.
        """
        # Generar QR si no existe
        if not self.qr_code:
            self.generar_qr()
        
        super().save(*args, **kwargs)

    def _sumar_meses(self, fecha_base, meses=1):
        """
        Suma meses a una fecha conservando el día cuando sea posible.
        """
        month_index = fecha_base.month - 1 + meses
        year = fecha_base.year + month_index // 12
        month = month_index % 12 + 1
        day = min(fecha_base.day, calendar.monthrange(year, month)[1])
        return fecha_base.replace(year=year, month=month, day=day)

    def registrar_revision(self, fecha_revision=None, meses_siguiente=1):
        """
        Actualiza las fechas del extintor después de registrar una revisión.
        """
        fecha_revision = fecha_revision or timezone.now().date()
        self.ultima_revision = fecha_revision
        self.proxima_revision = self._sumar_meses(fecha_revision, meses_siguiente)
        self.save(update_fields=['ultima_revision', 'proxima_revision', 'updated_at'])


class RevisionExtintor(models.Model):
    """
    Registro histórico de revisiones/inspecciones de un extintor.

    Guarda el payload completo que envía el frontend y también los campos
    normalizados para consulta y reportes.
    """

    ESTADO_COMPLETADO = 'completado'
    ESTADO_CON_OBSERVACIONES = 'con_observaciones'
    ESTADO_CHOICES = [
        (ESTADO_COMPLETADO, 'Completado'),
        (ESTADO_CON_OBSERVACIONES, 'Con observaciones'),
    ]

    TIPO_UIPC = 'uipc'
    TIPO_SERVICIO_CHOICES = [
        (TIPO_UIPC, 'UIPC'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )
    extintor = models.ForeignKey(
        Extintor,
        on_delete=models.CASCADE,
        related_name='revisiones',
        verbose_name='Extintor',
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='revisiones_extintor',
        verbose_name='Empresa',
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='revisiones_extintor',
        verbose_name='Técnico',
        null=True,
        blank=True,
    )
    tipo_servicio = models.CharField(
        max_length=20,
        choices=TIPO_SERVICIO_CHOICES,
        default=TIPO_UIPC,
        verbose_name='Tipo de servicio',
    )
    scope_type = models.CharField(
        max_length=20,
        default=Extintor.__name__.lower(),
        verbose_name='Scope type',
    )
    scope_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name='Scope ID',
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default=ESTADO_COMPLETADO,
        verbose_name='Estado',
    )
    respuestas_json = models.JSONField(default=dict, blank=True, verbose_name='Respuestas')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    observaciones_por_item = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Observaciones por ítem',
    )
    tiene_incidencias = models.BooleanField(default=False, verbose_name='Tiene incidencias')
    payload_json = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Payload original',
        help_text='Copia exacta del payload recibido desde el frontend.',
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Creado en')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Actualizado en')

    class Meta:
        db_table = 'extintores_revision'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['extintor', 'creado_en']),
            models.Index(fields=['empresa']),
            models.Index(fields=['scope_type', 'scope_id']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo_servicio']),
        ]

    def __str__(self):
        return f"Revision {self.tipo_servicio} - {self.extintor_id} ({self.estado})"
