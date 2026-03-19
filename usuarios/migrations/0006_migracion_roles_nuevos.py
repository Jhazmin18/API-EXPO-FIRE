# Generated manually for role migration.
from django.db import migrations, models


ROLE_MAP_FORWARD = {
    'ADMINISTRADOR': 'SUPERADMIN',
    'EMPRESA': 'ADMIN_EMPRESA',
    'CAMPO': 'ANALISTA',
}

ROLE_MAP_BACKWARD = {
    'SUPERADMIN': 'ADMINISTRADOR',
    'ADMIN_EMPRESA': 'EMPRESA',
    'SUPERVISOR': 'EMPRESA',
    'ANALISTA': 'CAMPO',
}


def migrate_roles_forward(apps, schema_editor):
    Perfil = apps.get_model('usuarios', 'Perfil')
    for old_role, new_role in ROLE_MAP_FORWARD.items():
        Perfil.objects.filter(rol=old_role).update(rol=new_role)


def migrate_roles_backward(apps, schema_editor):
    Perfil = apps.get_model('usuarios', 'Perfil')
    for new_role, old_role in ROLE_MAP_BACKWARD.items():
        Perfil.objects.filter(rol=new_role).update(rol=old_role)


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_perfil_domicilio_perfil_telefono_and_more'),
    ]

    operations = [
        migrations.RunPython(
            migrate_roles_forward,
            reverse_code=migrate_roles_backward,
        ),
        migrations.AlterField(
            model_name='perfil',
            name='rol',
            field=models.CharField(
                choices=[
                    ('SUPERADMIN', 'Expro Fire'),
                    ('ADMIN_EMPRESA', 'Admin. Empresa'),
                    ('SUPERVISOR', 'Supervisor General'),
                    ('ANALISTA', 'Analista'),
                ],
                default='ANALISTA',
                max_length=20,
                verbose_name='Rol',
            ),
        ),
    ]
