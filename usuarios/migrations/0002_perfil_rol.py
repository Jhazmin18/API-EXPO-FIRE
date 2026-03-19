from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        # El campo `rol` ya se definió originalmente en la migración inicial,
        # por lo que esta migración no ejecuta ninguna operación adicional.
    ]
