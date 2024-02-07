# Generated by Django 4.2 on 2024-01-30 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_alter_payment_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='payer_given_name',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payer_id',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payer_mail',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payer_surname',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]