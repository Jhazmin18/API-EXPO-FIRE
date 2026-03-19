# Generated manually for template permissions.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='formtemplate',
            name='roles_permitidos',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Lista de roles con acceso. Vacío = todos los roles.',
                verbose_name='Roles permitidos',
            ),
        ),
        migrations.AddField(
            model_name='formtemplate',
            name='empresas_permitidas',
            field=models.ManyToManyField(
                blank=True,
                help_text='Empresas con acceso. Vacío = todas las empresas.',
                related_name='templates_formulario_permitidos',
                to='empresas.empresa',
                verbose_name='Empresas permitidas',
            ),
        ),
    ]
