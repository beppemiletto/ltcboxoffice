# Generated by Django 4.2 on 2023-10-27 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fiscalmgm', '0005_ingresso_update_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='update_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]