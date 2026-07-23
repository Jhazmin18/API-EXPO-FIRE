"""
Regenera las imagenes QR de los extintores con el layout actual del modelo.

Uso:
    python scripts/regenerar_qrs_extintores.py

Con settings local:
    $env:DJANGO_SETTINGS_MODULE="core.settings_local"
    python scripts/regenerar_qrs_extintores.py
"""
import os
import sys
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

from extintores.models import Extintor


def main():
    total = 0

    for extintor in Extintor.objects.all().order_by('codigo'):
        if extintor.qr_code:
            extintor.qr_code.delete(save=False)

        extintor.generar_qr()
        extintor.save(update_fields=['qr_code', 'updated_at'])
        total += 1
        print(f'QR regenerado: {extintor.codigo}')

    print(f'\nListo. QR regenerados: {total}')


if __name__ == '__main__':
    main()
