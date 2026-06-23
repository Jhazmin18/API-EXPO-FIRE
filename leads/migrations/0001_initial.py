from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=180)),
                ('empresa', models.CharField(max_length=180)),
                ('correo', models.EmailField(max_length=254)),
                ('telefono', models.CharField(max_length=40)),
                ('servicio', models.CharField(max_length=160)),
                ('mensaje', models.TextField(blank=True)),
                ('captcha_success', models.BooleanField(default=False)),
                ('captcha_challenge_ts', models.DateTimeField(blank=True, null=True)),
                ('captcha_hostname', models.CharField(blank=True, max_length=255)),
                ('captcha_action', models.CharField(blank=True, max_length=255)),
                ('captcha_cdata', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Lead',
                'verbose_name_plural': 'Leads',
                'ordering': ['-created_at'],
            },
        ),
    ]
