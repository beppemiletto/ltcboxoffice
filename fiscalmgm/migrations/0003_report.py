# Generated by Django 4.2 on 2023-10-27 08:54

from django.db import migrations, models
import django.db.models.deletion
import pathlib


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_event_vat_rate'),
        ('fiscalmgm', '0002_alter_ingresso_sell_mode'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default='SIAE MOD 566', max_length=12)),
                ('doc_path', models.FilePathField(default='dummy.xls', editable=False, path=pathlib.PurePosixPath('/home/beppe/project/ltcboxoffice/media/siae_reports'), verbose_name='report file path')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.event')),
            ],
        ),
    ]