# Generated by Django 4.2 on 2023-05-16 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0004_cartitem_user_alter_cartitem_cart'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='ingresso',
            field=models.IntegerField(choices=[(0, 'Gratuito'), (1, 'Intero'), (2, 'Ridotto')], default=1),
        ),
    ]