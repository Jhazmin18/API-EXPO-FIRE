from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_perfil_empresa_fk'),
    ]

    operations = [
        # Este migration originalmente removía el campo `nombre_completo`,
        # pero ese campo nunca existió en la secuencia actual, así que se
        # deja como no-op para mantener el orden de migraciones.
    ]
