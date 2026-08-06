from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0007_empresa_activa_empresa_cajones_estacionamiento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='estatus',
            field=models.CharField(
                choices=[
                    ('VIGENTE', 'Vigente'),
                    ('BORRADA', 'Borrada'),
                ],
                default='VIGENTE',
                help_text='Control visual para ocultar la empresa en el frontend sin eliminarla.',
                max_length=20,
                verbose_name='Estatus',
            ),
        ),
    ]
