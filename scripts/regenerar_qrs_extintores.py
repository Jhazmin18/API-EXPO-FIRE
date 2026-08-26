"""
Regenera las imagenes QR de los extintores con el layout actual del modelo.

Uso:
    python scripts/regenerar_qrs_extintores.py --before 2026-01-01

Opcionalmente puedes cambiar el settings module:
    python scripts/regenerar_qrs_extintores.py --settings=core.settings_local --before 2026-01-01
"""
import os
import sys
import argparse
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

settings_module = 'core.settings'
clean_args = []
for arg in sys.argv[1:]:
    if arg.startswith('--settings='):
        settings_module = arg.split('=', 1)[1]
    else:
        clean_args.append(arg)
sys.argv = [sys.argv[0], *clean_args]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

import django

django.setup()

from django.utils.dateparse import parse_date
from extintores.models import Extintor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Regenera los QR de extintores creados antes de una fecha dada.',
    )
    parser.add_argument(
        '--before',
        required=True,
        help='Fecha límite en formato YYYY-MM-DD. Se regeneran extintores creados antes de ese día.',
    )
    return parser


def parse_before_date(raw_value: str) -> date:
    parsed = parse_date(raw_value)
    if parsed is None:
        raise ValueError(f'Fecha inválida: {raw_value}. Usa el formato YYYY-MM-DD.')
    return parsed


def main():
    parser = build_parser()
    args = parser.parse_args()

    before_date = parse_before_date(args.before)
    queryset = Extintor.objects.filter(created_at__date__lt=before_date).order_by('codigo')

    total = 0

    for extintor in queryset:
        if extintor.qr_code:
            extintor.qr_code.delete(save=False)

        extintor.generar_qr()
        extintor.save(update_fields=['qr_code', 'updated_at'])
        total += 1
        print(f'QR regenerado: {extintor.codigo} (creado: {extintor.created_at.date()})')

    print(f'\nListo. QR regenerados: {total}')
    print(f'Filtro aplicado: creados antes de {before_date.isoformat()}')


if __name__ == '__main__':
    main()
