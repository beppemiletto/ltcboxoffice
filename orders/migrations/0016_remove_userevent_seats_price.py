# Generated by Django 4.2 on 2024-05-03 10:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0015_alter_orderevent_expired'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userevent',
            name='seats_price',
        ),
    ]