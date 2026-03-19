from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_perfil_rol'),
        ('empresas', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='perfil',
            name='empresa',
        ),
        migrations.AddField(
            model_name='perfil',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='perfiles',
                to='empresas.empresa',
                verbose_name='Empresa'
            ),
        ),
    ]
