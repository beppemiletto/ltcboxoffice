# Generated by Django 4.2 on 2023-05-15 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='country',
        ),
        migrations.AddField(
            model_name='order',
            name='post_code',
            field=models.CharField(default=10020, max_length=10),
            preserve_default=False,
        ),
    ]