"""
Restablece la contrasena de los usuarios con ID del 1 al 7.

La nueva contrasena queda como:
    <username>12345

Uso:
    python scripts/resetear_passwords_usuario_1_7.py

Opcionalmente:
    python scripts/resetear_passwords_usuario_1_7.py --start-id 1 --end-id 7
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def bootstrap_django() -> None:
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    import django

    django.setup()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restablece la contrasena de usuarios por rango de ID."
    )
    parser.add_argument(
        "--start-id",
        type=int,
        default=1,
        help="ID inicial del rango (default: 1).",
    )
    parser.add_argument(
        "--end-id",
        type=int,
        default=7,
        help="ID final del rango (default: 7).",
    )
    return parser


def run(start_id: int, end_id: int) -> None:
    from django.contrib.auth import get_user_model

    User = get_user_model()

    if start_id > end_id:
        raise ValueError("--start-id no puede ser mayor que --end-id")

    total = 0
    for user_id in range(start_id, end_id + 1):
        user = User.objects.filter(id=user_id).first()
        if not user:
            print(f"- Usuario ID {user_id}: no encontrado")
            continue

        nueva_contrasena = f"{user.username}12345"
        user.set_password(nueva_contrasena)
        user.save(update_fields=["password"])
        total += 1

        print(f"- Usuario ID {user.id}: {user.username} -> {nueva_contrasena}")

    print(f"Usuarios actualizados: {total}")


def main() -> None:
    bootstrap_django()
    parser = build_parser()
    args = parser.parse_args()
    run(args.start_id, args.end_id)


if __name__ == "__main__":
    main()
