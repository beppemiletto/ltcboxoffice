# Generated by Django 4.2 on 2023-06-16 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0004_ticket_sell_mode_alter_ticket_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='seat',
            field=models.CharField(blank=True, default='C03', editable=False, max_length=3),
        ),
    ]
