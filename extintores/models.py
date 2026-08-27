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
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


def revision_pdf_upload_to(instance, _filename):
    empresa_id = getattr(instance.extintor, 'empresa_id', None) if getattr(instance, 'extintor_id', None) else None
    empresa_folder = f'empresa_{empresa_id}' if empresa_id else 'empresa_sin_asignar'
    extintor_id = getattr(instance, 'extintor_id', 'sin_extintor')
    return f'empresas/{empresa_folder}/uipc_pdfs/uipc_{extintor_id}_{uuid.uuid4().hex}.pdf'


import os
from django.conf import settings

def _load_font(size, bold=False):
    """
    Carga una fuente disponible tanto en Windows como en Linux/Railway.
    Prioriza la fuente empacada en el repo para no depender de lo que
    tenga instalado el sistema operativo del contenedor.
    """
    font_file = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    project_font = os.path.join(settings.BASE_DIR, 'static', 'fonts', font_file)

    candidates = [
        project_font,
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

    # Antes esto caía en ImageFont.load_default() en silencio, que ignora
    # 'size' por completo y produce etiquetas ilegibles. Mejor fallar fuerte.
    raise RuntimeError(
        f"No se encontró ninguna fuente TrueType válida (tamaño={size}, bold={bold}). "
        f"Verifica que {project_font} exista en el contenedor."
    )

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
        # --- DIMENSIONES PARA BRADY M21-750-499 (19.05mm x 66mm a 203 DPI) ---
        label_width = 527   # 66 mm
        label_height = 152  # 19.05 mm
        margin = 4
        gap = 14

        # 1. Generar QR
        qr = segno.make(self.get_qr_url(), error='l')
        qr_buffer = BytesIO()
        qr.save(qr_buffer, kind='png', scale=6, border=1, dark='#000000', light='white')
        qr_buffer.seek(0)
        qr_img = Image.open(qr_buffer).convert('RGB')

        # Ajustar QR al alto completo (~144px)
        qr_size = label_height - (margin * 2)
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS
        qr_img = qr_img.resize((qr_size, qr_size), resample_filter)

        # 2. Lienzo blanco
        combined = Image.new('RGB', (label_width, label_height), 'white')
        combined.paste(qr_img, (margin, margin))

        draw = ImageDraw.Draw(combined)

        # 3. FUENTES MUCHO MÁS GRANDES Y EN NEGRITA (Mínimo 38px a 46px)
        title_font = _load_font(26, bold=True)  # Código grande
        text_font = _load_font(18, bold=True)   # Ubicacion + Capacidad
        small_font = _load_font(16, bold=True)  # Fecha Vencimiento

        text_x = margin + qr_size + gap
        text_width = label_width - text_x - margin
        y = margin + 2

        def truncate_text(text, font, max_width):
            text = str(text or '')
            if draw.textlength(text, font=font) <= max_width:
                return text
            ellipsis = '...'
            while text and draw.textlength(f'{text}{ellipsis}', font=font) > max_width:
                text = text[:-1]
            return f'{text}{ellipsis}' if text else ellipsis

        # LÍNEA 1: Código (Texto principal en negrilla)
        draw.text((text_x, y), truncate_text(self.codigo, title_font, text_width), fill='black', font=title_font)
        title_bbox = draw.textbbox((0, 0), 'Ag', font=title_font)
        y += (title_bbox[3] - title_bbox[1]) + 2

        # LÍNEA 2: Ubicacion
        draw.text((text_x, y), truncate_text(f'Ubicacion: {self.ubicacion}', text_font, text_width), fill='black', font=text_font)
        text_bbox = draw.textbbox((0, 0), 'Ag', font=text_font)
        y += (text_bbox[3] - text_bbox[1]) + 2

        # LÍNEA 3: Capacidad
        draw.text((text_x, y), truncate_text(f'Capacidad: {self.capacidad}', text_font, text_width), fill='black', font=text_font)
        text_bbox = draw.textbbox((0, 0), 'Ag', font=text_font)
        y += (text_bbox[3] - text_bbox[1]) + 2

        # LÍNEA 4: Vencimiento
        fecha_venc = self.fecha_vencimiento.strftime('%d/%m/%Y') if self.fecha_vencimiento else 'S/F'
        draw.text((text_x, y), truncate_text(f'Vence: {fecha_venc}', small_font, text_width), fill='black', font=small_font)

        return combined
    def obtener_etiqueta_png(self):
        combined = self._build_label_image()
        buffer = BytesIO()
        combined.save(buffer, format='PNG', dpi=(300, 300))
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
        combined.save(buffer, format='PNG', dpi=(300, 300))
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
    pdf_uipc = models.FileField(
        upload_to=revision_pdf_upload_to,
        blank=True,
        null=True,
        verbose_name='PDF UIPC',
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

    def _format_bool(self, value):
        return 'Si' if value is True else 'No' if value is False else '-'

    def _uipc_sections(self):
        return [
            (
                'Ubicación y accesibilidad',
                [
                    {
                        'key': 'visible_legible_accesible',
                        'label': '¿El extintor está visible, legible y accesible, sin obstrucciones?',
                        'norma': 'NOM-002-STPS-2010 §4.1',
                        'aliases': ['visible_legible_accesible', 'visible', 'accesible', 'obstrucciones'],
                    },
                    {
                        'key': 'lugar_asignado',
                        'label': '¿El extintor se encuentra en el lugar asignado (soporte o nicho)?',
                        'norma': 'NOM-002-STPS-2010 §4.2',
                        'aliases': ['lugar_asignado', 'soporte_nicho', 'ubicacion_correcta'],
                    },
                    {
                        'key': 'senalizacion',
                        'label': '¿La señalización del extintor está visible y en buen estado?',
                        'norma': 'NOM-026-STPS-2008',
                        'aliases': ['senalizacion', 'señalizacion', 'seÃ±alizacion', 'senal_visible'],
                    },
                ],
            ),
            (
                'Condición del equipo',
                [
                    {
                        'key': 'manometro',
                        'label': '¿El manómetro indica presión correcta (aguja en zona verde)?',
                        'norma': 'NOM-154-SCFI-2005 §7.3',
                        'aliases': ['manometro', 'manómetro', 'presion_correcta'],
                    },
                    {
                        'key': 'pasador',
                        'label': '¿El pasador de seguridad está en su lugar e intacto?',
                        'norma': 'NOM-154-SCFI-2005 §7.4',
                        'aliases': ['pasador', 'pasador_intacto'],
                    },
                    {
                        'key': 'precinto',
                        'label': '¿El precinto de seguridad está intacto (sin señales de uso)?',
                        'norma': 'NOM-154-SCFI-2005 §7.4',
                        'aliases': ['precinto', 'precinto_intacto', 'sello'],
                    },
                    {
                        'key': 'cuerpo',
                        'label': '¿El cuerpo del extintor está en buen estado (sin golpes, corrosión ni deformaciones)?',
                        'norma': 'NOM-154-SCFI-2005 §7.5',
                        'aliases': ['cuerpo', 'cuerpo_buen_estado', 'sin_golpes'],
                    },
                    {
                        'key': 'manguera',
                        'label': '¿La manguera, boquilla y válvula están en buen estado y sin obstrucciones?',
                        'norma': 'NOM-154-SCFI-2005 §7.6',
                        'aliases': ['manguera', 'boquilla', 'valvula', 'válvula'],
                    },
                ],
            ),
            (
                'Vigencia y documentación',
                [
                    {
                        'key': 'etiqueta',
                        'label': '¿La etiqueta de mantenimiento está presente y vigente?',
                        'norma': 'NOM-154-SCFI-2005 §8',
                        'aliases': ['etiqueta', 'etiqueta_mantenimiento', 'mantenimiento_vigente'],
                    },
                    {
                        'key': 'fecha_proximo_mantenimiento',
                        'label': '¿La fecha de próximo mantenimiento está vigente?',
                        'norma': 'NOM-002-STPS-2010 §6.3',
                        'aliases': ['fecha_proximo_mantenimiento', 'fecha_proxima', 'proximo_mantenimiento', 'proxima_revision'],
                    },
                ],
            ),
        ]

    def _resolve_uipc_answer(self, respuestas, question):
        aliases = [question['key'], *question.get('aliases', [])]
        for key in aliases:
            if key in respuestas:
                return respuestas.get(key)
        return None

    def _render_uipc_question(self, pregunta, respuesta, observaciones_por_item, body_style, small_style):
        if isinstance(respuesta, bool):
            response_text = 'Sí' if respuesta else 'No'
            response_color = '#166534' if respuesta else '#B45309'
        elif respuesta in (None, ''):
            response_text = '-'
            response_color = '#6B7280'
        else:
            response_text = str(respuesta)
            response_color = '#374151'

        observacion = observaciones_por_item.get(pregunta['key'])
        if observacion in (None, '') and not bool(respuesta):
            observacion = observaciones_por_item.get(pregunta['label'])

        left_parts = [
            f"<b>{pregunta['label']}</b>",
            f"<font size='8' color='#6B7280'>{pregunta['norma']}</font>",
        ]
        if observacion:
            if respuesta is False:
                left_parts.append("<font size='8' color='#FF7F00'><b>¿Por qué no cumple este punto?</b></font>")
            left_parts.append(f"<font size='8' color='#B45309'>Observación: {observacion}</font>")

        left_para = Paragraph('<br/>'.join(left_parts), body_style)
        right_para = Paragraph(
            f"<font color='{response_color}'><b>{response_text}</b></font>",
            small_style,
        )
        return [left_para, right_para]

    def _build_uipc_pdf(self):
        buffer = BytesIO()
        accent = colors.HexColor('#FF7F00')
        accent_dark = colors.HexColor('#B45309')
        muted = colors.HexColor('#6B7280')
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'UIPCTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#111827'),
            alignment=TA_LEFT,
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            'UIPCSubtitle',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=muted,
            spaceAfter=4,
        )
        section_style = ParagraphStyle(
            'UIPCSection',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor('#374151'),
            spaceBefore=7,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            'UIPCBody',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=8.7,
            leading=10.5,
            textColor=colors.HexColor('#111827'),
        )
        small_style = ParagraphStyle(
            'UIPCSmall',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor('#111827'),
            alignment=TA_LEFT,
        )
        note_style = ParagraphStyle(
            'UIPCNote',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=accent_dark,
        )

        respuestas = self.respuestas_json or {}
        observaciones_item = self.observaciones_por_item or {}
        observaciones_generales = (self.observaciones or '').strip() or str(respuestas.get('observaciones') or '').strip()
        ext = self.extintor
        empresa = self.empresa
        tecnico = self.tecnico
        creado_en = self.creado_en
        fecha_documento = creado_en.strftime('%d/%m/%Y %H:%M') if creado_en else timezone.now().strftime('%d/%m/%Y %H:%M')
        fecha_archivo = creado_en.strftime('%Y%m%d') if creado_en else timezone.now().strftime('%Y%m%d')
        folio = f'UIPC-{fecha_archivo}-{self.id.hex[:8].upper()}'

        story = []
        story.append(Paragraph('UIPC de Extintor', title_style))
        story.append(Paragraph('Documento generado automaticamente a partir del registro de revision.', subtitle_style))
        story.append(Paragraph(f'Folio: {folio}', subtitle_style))
        story.append(Paragraph(f'Fecha de generacion: {fecha_documento}', subtitle_style))
        story.append(Spacer(1, 3 * mm))

        summary_rows = [
            ['Extintor', ext.codigo if ext else '-'],
            ['Empresa', empresa.nombre if empresa else '-'],
            ['Ubicacion', ext.ubicacion if ext else '-'],
            ['Fecha de revision', creado_en.strftime('%d/%m/%Y %H:%M') if creado_en else '-'],
            ['Tecnico', tecnico.get_full_name() if tecnico and tecnico.get_full_name() else (tecnico.username if tecnico else '-')],
            ['Estado', self.estado.replace('_', ' ').title()],
            ['Incidencias', 'Sí' if self.tiene_incidencias else 'No'],
        ]
        summary = Table(summary_rows, colWidths=[42 * mm, 118 * mm])
        summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
            ('LINEBEFORE', (0, 0), (0, -1), 1.2, accent),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.8),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#E5E7EB')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(summary)

        for section_title, preguntas in self._uipc_sections():
            story.append(Spacer(1, 4 * mm))
            story.append(Paragraph(section_title, section_style))

            rows = [['Pregunta', 'Respuesta']]
            for pregunta in preguntas:
                respuesta = self._resolve_uipc_answer(respuestas, pregunta)
                rows.append(self._render_uipc_question(pregunta, respuesta, observaciones_item, body_style, small_style))

            table = Table(rows, colWidths=[124 * mm, 36 * mm], repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.2),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#D1D5DB')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ]))
            story.append(table)

        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph('Observaciones adicionales', section_style))
        if observaciones_generales:
            story.append(Paragraph(observaciones_generales, note_style))
        else:
            story.append(Paragraph('Sin observaciones adicionales.', note_style))

        story.append(Spacer(1, 6 * mm))
        footer_rows = [[
            Paragraph(
                'EXPRO FIRE',
                ParagraphStyle(
                    'FooterBrand',
                    parent=body_style,
                    fontName='Helvetica-Bold',
                    textColor=accent,
                    fontSize=10,
                ),
            ),
            Paragraph(
                'Revision UIPC generada desde el sistema',
                ParagraphStyle(
                    'FooterText',
                    parent=body_style,
                    alignment=TA_LEFT,
                    textColor=colors.HexColor('#6B7280'),
                ),
            ),
        ]]
        footer = Table(footer_rows, colWidths=[35 * mm, 125 * mm])
        footer.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('LINEABOVE', (0, 0), (-1, 0), 0.6, accent),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(footer)

        def draw_page(canvas, doc):
            canvas.saveState()
            width, height = A4
            canvas.setFillColor(colors.white)
            canvas.rect(0, 0, width, height, stroke=0, fill=1)
            canvas.setFillColor(colors.HexColor('#E5E7EB'))
            canvas.rect(0, 0, width, 3, stroke=0, fill=1)
            canvas.setFillColor(accent)
            canvas.setFont('Helvetica-Bold', 10)
            canvas.drawString(doc.leftMargin, height - 19, 'EXPRO FIRE')
            canvas.setFont('Helvetica', 8)
            canvas.drawRightString(width - doc.rightMargin, height - 18, fecha_documento)
            canvas.drawRightString(width - doc.rightMargin, height - 28, folio)
            canvas.drawRightString(width - doc.rightMargin, 10, f'Pagina {canvas.getPageNumber()}')
            canvas.restoreState()

        doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
        buffer.seek(0)
        return buffer

    def generar_pdf_uipc(self, save=True):
        if not self.pk:
            raise ValueError('La revision debe estar guardada antes de generar el PDF.')

        pdf_buffer = self._build_uipc_pdf()
        fecha_archivo = self.creado_en.strftime('%Y%m%d') if self.creado_en else timezone.now().strftime('%Y%m%d')
        filename = f'uipc_{self.extintor_id}_{fecha_archivo}_{self.id.hex[:8].upper()}.pdf'
        self.pdf_uipc.save(filename, ContentFile(pdf_buffer.getvalue()), save=False)
        pdf_buffer.close()

        if save:
            super().save(update_fields=['pdf_uipc', 'actualizado_en'])
