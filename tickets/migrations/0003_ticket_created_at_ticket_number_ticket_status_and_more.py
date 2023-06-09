# Generated by Django 4.2 on 2023-06-15 15:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_remove_ticket_event_ticket_orderevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='number',
            field=models.CharField(blank=True, default='', max_length=25),
        ),
        migrations.AddField(
            model_name='ticket',
            name='status',
            field=models.CharField(choices=[('New', 'New'), ('Printed', 'Printed'), ('Obliterated', 'Obliterated'), ('Cancelled', 'Cancelled')], default='New', max_length=12),
        ),
        migrations.AddField(
            model_name='ticket',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
