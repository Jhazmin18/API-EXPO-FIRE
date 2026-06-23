from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='email_enviado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lead',
            name='email_enviado_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='email_error',
            field=models.TextField(blank=True),
        ),
    ]
