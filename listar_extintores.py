"""
Script para ver los extintores existentes
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from extintores.models import Extintor

# Listar todos los extintores
extintores = Extintor.objects.all()

print(f"Total de extintores: {extintores.count()}")
print("-" * 50)

for ext in extintores:
    print(f"ID: {ext.id}")
    print(f"Codigo: {ext.codigo}")
    print(f"Ubicacion: {ext.ubicacion}")
    print(f"Tipo: {ext.tipo}")
    print(f"Estado: {ext.estado}")
    print(f"Dias para vencer: {ext.dias_para_vencer}")
    print(f"QR generado: {bool(ext.qr_code)}")
    print("-" * 50)

