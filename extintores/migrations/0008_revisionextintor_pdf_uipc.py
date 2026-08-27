from django.db import migrations, models
import extintores.models


class Migration(migrations.Migration):

    dependencies = [
        ('extintores', '0007_revisionextintor'),
    ]

    operations = [
        migrations.AddField(
            model_name='revisionextintor',
            name='pdf_uipc',
            field=models.FileField(blank=True, null=True, upload_to=extintores.models.revision_pdf_upload_to, verbose_name='PDF UIPC'),
        ),
    ]
