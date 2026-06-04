from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('usuarios', '0007_merge_0002_and_0006'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='requiere_cambio_password',
            field=models.BooleanField(default=False, verbose_name='Requiere cambio de contraseña'),
        ),
        migrations.AddField(
            model_name='perfil',
            name='reset_password_solicitado_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de solicitud de reseteo'),
        ),
        migrations.AddField(
            model_name='perfil',
            name='reset_password_solicitado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='resets_password_solicitados',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Reseteo solicitado por',
            ),
        ),
    ]
