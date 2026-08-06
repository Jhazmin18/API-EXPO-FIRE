from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0003_formtemplate_header_requiere_en_establecimiento'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='formrun',
            name='tecnico',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='formularios',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Técnico',
            ),
        ),
        migrations.AddField(
            model_name='formrun',
            name='observaciones',
            field=models.TextField(blank=True, null=True, verbose_name='Observaciones'),
        ),
        migrations.AddField(
            model_name='formrun',
            name='observaciones_por_item',
            field=models.JSONField(blank=True, default=dict, verbose_name='Observaciones por ítem'),
        ),
    ]
