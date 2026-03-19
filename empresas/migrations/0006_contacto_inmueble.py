from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0005_merge_0002_and_0004'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contacto',
            name='extintor',
        ),
        migrations.AddField(
            model_name='empresa',
            name='tipo_inmueble',
            field=models.CharField(
                blank=True,
                help_text='Ej: Hospital, Guardería, Planta industrial',
                max_length=150,
                verbose_name='Tipo de inmueble',
            ),
        ),
    ]
