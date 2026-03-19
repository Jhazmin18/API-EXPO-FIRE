"""
Script temporal para crear un extintor de prueba
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from extintores.models import Extintor
from datetime import date

# Crear extintor de prueba
extintor = Extintor.objects.create(
    codigo='EXT-001',
    ubicacion='Planta Baja - Pasillo Principal',
    tipo='CO2',
    capacidad='5kg',
    fecha_fabricacion=date(2023, 1, 1),
    fecha_vencimiento=date(2028, 1, 1),
    proxima_revision=date(2026, 6, 1),
    observaciones='Extintor de prueba creado automáticamente'
)

print(f"OK - Extintor creado exitosamente!")
print(f"   ID: {extintor.id}")
print(f"   Codigo: {extintor.codigo}")
print(f"   Ubicacion: {extintor.ubicacion}")
print(f"   Estado: {extintor.estado}")
print(f"   Dias para vencer: {extintor.dias_para_vencer}")
print(f"   QR generado: {bool(extintor.qr_code)}")

