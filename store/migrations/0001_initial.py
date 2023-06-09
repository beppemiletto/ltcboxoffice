# Generated by Django 4.2 on 2023-04-23 07:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('billboard', '0005_alter_show_responsible_mail'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField()),
                ('price_full', models.FloatField()),
                ('price_reduced', models.FloatField()),
                ('event_slug', models.SlugField(max_length=200, unique=True)),
                ('show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='billboard.show')),
            ],
        ),
    ]
