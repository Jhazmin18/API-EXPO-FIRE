from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extintores', '0005_extintor_clase_fuego_extintor_modalidad_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extintor',
            name='codigo',
            field=models.CharField(
                help_text='Código único del extintor (ej: EXT-001)',
                max_length=50,
                verbose_name='Código',
            ),
        ),
        migrations.AddConstraint(
            model_name='extintor',
            constraint=models.UniqueConstraint(
                fields=('empresa', 'codigo'),
                name='unique_extintor_codigo_por_empresa',
            ),
        ),
        migrations.AddIndex(
            model_name='extintor',
            index=models.Index(fields=['empresa', 'codigo'], name='ext_empresa_codigo_idx'),
        ),
    ]
