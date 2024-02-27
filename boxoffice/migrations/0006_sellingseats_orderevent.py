# Generated by Django 4.2 on 2024-02-14 13:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_orderevent_expired'),
        ('boxoffice', '0005_boxofficetransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='sellingseats',
            name='orderevent',
            field=models.ForeignKey(default=9, on_delete=django.db.models.deletion.CASCADE, to='orders.orderevent'),
            preserve_default=False,
        ),
    ]
