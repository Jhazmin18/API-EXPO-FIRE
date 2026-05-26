"""
Script para crear una empresa y un extintor de prueba.

Uso rápido:
    python scripts/crear_extintor_test.py

Ejemplo con datos personalizados:
    python scripts/crear_extintor_test.py --empresa "Grupo Demo" --codigo EXT-101 --ubicacion "Planta Alta"
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path


def bootstrap_django() -> None:
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    import django

    django.setup()


def parse_date(value: str | None, fallback: date | None) -> date | None:
    if value in (None, ""):
        return fallback
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crea o actualiza una empresa y varios extintores de ejemplo en el sistema."
    )
    parser.add_argument("--empresa", default="Empresa Prueba", help="Nombre de la empresa.")
    parser.add_argument(
        "--razon-social",
        default="Empresa Prueba S.A. de C.V.",
        help="Razón social de la empresa.",
    )
    parser.add_argument(
        "--tipo-inmueble",
        default="Nave industrial",
        help="Tipo de inmueble de la empresa.",
    )
    parser.add_argument(
        "--cantidad",
        type=int,
        default=5,
        help="Cantidad de extintores de prueba a crear (mínimo recomendado: 5).",
    )
    parser.add_argument(
        "--usuario",
        default=None,
        help="Nombre de usuario para asignar como creador, si existe.",
    )
    return parser


def run(args: argparse.Namespace) -> None:
    from django.contrib.auth import get_user_model

    from empresas.models import Empresa
    from extintores.models import Extintor

    User = get_user_model()

    creado_por = None
    if args.usuario:
        creado_por = User.objects.filter(username=args.usuario).first()
        if not creado_por:
            print(f"Aviso: no se encontró el usuario '{args.usuario}'. Se creará sin creador.")

    empresa_defaults = {
        "razon_social": args.razon_social,
        "tipo_inmueble": args.tipo_inmueble,
        "activa": True,
    }
    if creado_por:
        empresa_defaults["creado_por"] = creado_por

    empresa, empresa_created = Empresa.objects.update_or_create(
        nombre=args.empresa,
        defaults=empresa_defaults,
    )

    print("Empresa:", "creada" if empresa_created else "actualizada")
    print(f"  ID: {empresa.id}")
    print(f"  Nombre: {empresa.nombre}")
    print(f"  Razón social: {empresa.razon_social}")

    plantillas = [
        {
            "codigo": "EXT-001",
            "ubicacion": "Planta Baja - Pasillo Principal",
            "tipo": "CO2",
            "capacidad": "5kg",
            "fecha_fabricacion": date(2023, 1, 1),
            "fecha_vencimiento": date(2028, 1, 1),
            "proxima_revision": date(2026, 6, 1),
            "observaciones": "Extintor cerca del acceso principal.",
        },
        {
            "codigo": "EXT-002",
            "ubicacion": "Recepción",
            "tipo": "PQS_ABC",
            "capacidad": "10kg",
            "fecha_fabricacion": date(2022, 5, 15),
            "fecha_vencimiento": date(2027, 5, 15),
            "proxima_revision": date(2026, 4, 20),
            "observaciones": "Ubicado junto al área de atención.",
        },
        {
            "codigo": "EXT-003",
            "ubicacion": "Almacén de materiales",
            "tipo": "ESPUMA",
            "capacidad": "9L",
            "fecha_fabricacion": date(2024, 2, 10),
            "fecha_vencimiento": date(2029, 2, 10),
            "proxima_revision": date(2026, 9, 15),
            "observaciones": "Protección para líquidos inflamables.",
        },
        {
            "codigo": "EXT-004",
            "ubicacion": "Sala de máquinas",
            "tipo": "AGUA",
            "capacidad": "6L",
            "fecha_fabricacion": date(2021, 8, 30),
            "fecha_vencimiento": date(2026, 8, 30),
            "proxima_revision": date(2026, 5, 25),
            "observaciones": "Extintor para uso en zona técnica.",
        },
        {
            "codigo": "EXT-005",
            "ubicacion": "Pasillo de oficinas",
            "tipo": "ACETATO_K",
            "capacidad": "6L",
            "fecha_fabricacion": date(2023, 11, 5),
            "fecha_vencimiento": date(2028, 11, 5),
            "proxima_revision": date(2026, 12, 1),
            "observaciones": "Cubre el bloque administrativo.",
        },
    ]

    tipos_validos = {choice[0] for choice in Extintor.AGENTE_CHOICES}
    creados = 0

    for index in range(max(args.cantidad, 5)):
        plantilla = plantillas[index % len(plantillas)].copy()
        if index >= len(plantillas):
            sufijo = index + 1
            plantilla["codigo"] = f"EXT-{sufijo:03d}"
            plantilla["ubicacion"] = f"Área adicional {sufijo}"
            plantilla["observaciones"] = f"Extintor de prueba número {sufijo}."
            plantilla["tipo"] = plantillas[index % len(plantillas)]["tipo"]
        if plantilla["tipo"] not in tipos_validos:
            plantilla["tipo"] = "PQS_ABC"

        defaults = {
            "ubicacion": plantilla["ubicacion"],
            "tipo": plantilla["tipo"],
            "capacidad": plantilla["capacidad"],
            "fecha_fabricacion": plantilla["fecha_fabricacion"],
            "fecha_vencimiento": plantilla["fecha_vencimiento"],
            "proxima_revision": plantilla["proxima_revision"],
            "observaciones": plantilla["observaciones"],
            "empresa": empresa,
        }
        if creado_por:
            defaults["creado_por"] = creado_por

        extintor, extintor_created = Extintor.objects.update_or_create(
            codigo=plantilla["codigo"],
            defaults=defaults,
        )
        creados += 1

        estado_accion = "creado" if extintor_created else "actualizado"
        print(f"- Extintor {plantilla['codigo']} {estado_accion}")
        print(f"  Ubicación: {extintor.ubicacion}")
        print(f"  Tipo: {extintor.get_tipo_display()}")
        print(f"  Capacidad: {extintor.capacidad}")
        print(f"  Estado: {extintor.estado}")
        print(f"  Días para vencer: {extintor.dias_para_vencer}")
        print(f"  QR generado: {bool(extintor.qr_code)}")

    print(f"Total de extintores procesados: {creados}")


def main() -> None:
    bootstrap_django()
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
