# models.py (app extintores)
"""
Modelos de la aplicación de gestión de extintores

Este módulo define el modelo Extintor que representa un extintor
en el sistema de gestión.
"""
import os
import uuid
import segno
from io import BytesIO
from django.db import models
from django.conf import settings
from django.core.files import File
from django.utils.functional import cached_property
from django.utils import timezone
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont

from empresas.models import Empresa


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
        unique=True,
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
        upload_to='qr_codes/',
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
        indexes = [
            models.Index(fields=['codigo']),
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
        return f"{self.QR_BASE_URL}{self.codigo}"

    def _build_label_image(self):
        qr = segno.make(self.get_qr_url(), error='h')
        qr_buffer = BytesIO()
        qr.save(qr_buffer, kind='png', scale=8, border=2, dark='#0c2340', light='white')
        qr_buffer.seek(0)
        img = Image.open(qr_buffer).convert('RGB')
        label_height = 90
        combined = Image.new('RGB', (img.width, img.height + label_height), 'white')
        combined.paste(img, (0, 0))
        draw = ImageDraw.Draw(combined)
        font = ImageFont.load_default()
        draw.text((10, img.height + 5), f"{self.codigo} - {self.get_tipo_display()}", fill='#102347', font=font)
        draw.text((10, img.height + 25), f"Ubicación: {self.ubicacion}", fill='gray', font=font)
        draw.text((10, img.height + 40), f"Capacidad: {self.capacidad}", fill='gray', font=font)
        fecha_venc = self.fecha_vencimiento.strftime('%Y-%m-%d') if self.fecha_vencimiento else 'Sin fecha'
        draw.text((10, img.height + 55), f"Vence: {fecha_venc}", fill='gray', font=font)
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
        filename = f'qr_{self.codigo}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar el QR automáticamente.
        """
        # Generar QR si no existe
        if not self.qr_code:
            self.generar_qr()
        
        super().save(*args, **kwargs)
