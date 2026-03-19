# Generated manually for template header behavior.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0002_formtemplate_permisos'),
    ]

    operations = [
        migrations.AddField(
            model_name='formtemplate',
            name='header_requiere_en_establecimiento',
            field=models.BooleanField(
                default=False,
                help_text='Si está activo, el frontend debe preguntar si se encuentra en el establecimiento y, cuando responda "no", pedir referencia abierta.',
                verbose_name='Header: requiere pregunta en establecimiento',
            ),
        ),
    ]
