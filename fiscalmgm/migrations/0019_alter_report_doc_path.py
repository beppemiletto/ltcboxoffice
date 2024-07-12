# Generated by Django 4.2 on 2024-07-05 21:16

from django.db import migrations, models
import pathlib


class Migration(migrations.Migration):

    dependencies = [
        ('fiscalmgm', '0018_alter_report_doc_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='doc_path',
            field=models.FilePathField(default='dummy.xls', editable=False, path=pathlib.PurePosixPath('/home/ltc/projects/ltcboxoffice/media/siae_reports'), verbose_name='report file path'),
        ),
    ]