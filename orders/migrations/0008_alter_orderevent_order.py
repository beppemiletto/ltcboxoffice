# Generated by Django 4.2 on 2023-07-11 08:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_userevent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderevent',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.order'),
        ),
    ]
