import argparse
import os
import sys
from pathlib import Path


def bootstrap_django():
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    import django

    django.setup()


def run(password: str):
    from django.contrib.auth import get_user_model

    from empresas.models import Empresa
    from usuarios.models import Perfil

    User = get_user_model()

    empresa, _ = Empresa.objects.get_or_create(
        nombre="Empresa Prueba",
        defaults={"razon_social": "Empresa Prueba S.A. de C.V."},
    )

    usuarios = [
        {
            "username": "superadmin_prueba",
            "email": "administrador@prueba.com",
            "first_name": "Super",
            "last_name": "Admin",
            "rol": Perfil.ROLE_SUPERADMIN,
            "empresa": None,
            "telefono": "5551000001",
            "domicilio": "Oficina Central Expro Fire",
            "is_staff": True,
            "is_superuser": True,
        },
        {
            "username": "admin_empresa_prueba",
            "email": "admin_empresa@prueba.com",
            "first_name": "Admin",
            "last_name": "Empresa",
            "rol": Perfil.ROLE_ADMIN_EMPRESA,
            "empresa": empresa,
            "telefono": "5551000002",
            "domicilio": "Corporativo Empresa Prueba",
            "is_staff": False,
            "is_superuser": False,
        },
        {
            "username": "supervisor_prueba",
            "email": "supervisor@prueba.com",
            "first_name": "Supervisor",
            "last_name": "General",
            "rol": Perfil.ROLE_SUPERVISOR,
            "empresa": empresa,
            "telefono": "5551000003",
            "domicilio": "Sucursal Norte Empresa Prueba",
            "is_staff": False,
            "is_superuser": False,
        },
        {
            "username": "analista_prueba",
            "email": "analista@prueba.com",
            "first_name": "Analista",
            "last_name": "Campo",
            "rol": Perfil.ROLE_ANALISTA,
            "empresa": empresa,
            "telefono": "5551000004",
            "domicilio": "Zona Operativa Empresa Prueba",
            "is_staff": False,
            "is_superuser": False,
        },
    ]

    for data in usuarios:
        defaults = {
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "is_staff": data["is_staff"],
            "is_superuser": data["is_superuser"],
            "is_active": True,
        }
        user, created = User.objects.get_or_create(
            username=data["username"],
            defaults=defaults,
        )
        if not created:
            for field, value in defaults.items():
                setattr(user, field, value)
        user.set_password(password)
        user.save()

        Perfil.objects.update_or_create(
            user=user,
            defaults={
                "rol": data["rol"],
                "empresa": data["empresa"],
                "telefono": data["telefono"],
                "domicilio": data["domicilio"],
            },
        )

        estado = "creado" if created else "actualizado"
        print(f"- {data['username']} ({data['rol']}) {estado}")

    print("Usuarios demo de roles listos.")


def main():
    parser = argparse.ArgumentParser(
        description="Crea/actualiza usuarios demo para cada rol nuevo."
    )
    parser.add_argument(
        "--password",
        default="12345678",
        help="Contrasena para todos los usuarios demo (default: 12345678).",
    )
    args = parser.parse_args()

    bootstrap_django()
    run(args.password)


if __name__ == "__main__":
    main()
