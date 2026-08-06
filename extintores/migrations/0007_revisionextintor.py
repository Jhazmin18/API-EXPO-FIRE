from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('extintores', '0006_extintor_codigo_por_empresa'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RevisionExtintor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_servicio', models.CharField(choices=[('uipc', 'UIPC')], default='uipc', max_length=20, verbose_name='Tipo de servicio')),
                ('scope_type', models.CharField(default='extintor', max_length=20, verbose_name='Scope type')),
                ('scope_id', models.CharField(db_index=True, max_length=64, verbose_name='Scope ID')),
                ('estado', models.CharField(choices=[('completado', 'Completado'), ('con_observaciones', 'Con observaciones')], default='completado', max_length=30, verbose_name='Estado')),
                ('respuestas_json', models.JSONField(blank=True, default=dict, verbose_name='Respuestas')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('observaciones_por_item', models.JSONField(blank=True, default=dict, verbose_name='Observaciones por ítem')),
                ('tiene_incidencias', models.BooleanField(default=False, verbose_name='Tiene incidencias')),
                ('payload_json', models.JSONField(blank=True, default=dict, help_text='Copia exacta del payload recibido desde el frontend.', verbose_name='Payload original')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Creado en')),
                ('actualizado_en', models.DateTimeField(auto_now=True, verbose_name='Actualizado en')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='revisiones_extintor', to='empresas.empresa', verbose_name='Empresa')),
                ('extintor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='revisiones', to='extintores.extintor', verbose_name='Extintor')),
                ('tecnico', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='revisiones_extintor', to=settings.AUTH_USER_MODEL, verbose_name='Técnico')),
            ],
            options={
                'db_table': 'extintores_revision',
                'ordering': ['-creado_en'],
                'indexes': [
                    models.Index(fields=['extintor', 'creado_en'], name='ext_revision_ext_creado_idx'),
                    models.Index(fields=['empresa'], name='ext_revision_emp_idx'),
                    models.Index(fields=['scope_type', 'scope_id'], name='ext_revision_scope_idx'),
                    models.Index(fields=['estado'], name='ext_revision_estado_idx'),
                    models.Index(fields=['tipo_servicio'], name='ext_revision_tipo_idx'),
                ],
            },
        ),
    ]
