# Generated by Django 4.2 on 2023-05-23 12:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_rename_items_orderevent_seat_orderevent_ingresso'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderevent',
            old_name='seat',
            new_name='seats_price',
        ),
        migrations.RemoveField(
            model_name='orderevent',
            name='ingresso',
        ),
        migrations.RemoveField(
            model_name='orderevent',
            name='order_price',
        ),
        migrations.RemoveField(
            model_name='orderevent',
            name='ordered',
        ),
    ]