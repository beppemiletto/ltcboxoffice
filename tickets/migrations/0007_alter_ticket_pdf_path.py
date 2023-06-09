# Generated by Django 4.2 on 2023-06-19 08:46

from django.db import migrations, models
import pathlib


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_ticket_pdf_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='pdf_path',
            field=models.FilePathField(default='dummy.pdf', editable=False, path=pathlib.PurePosixPath('/home/beppe/project/ltcboxoffice/media/tickets'), verbose_name='pdf file path'),
        ),
    ]
