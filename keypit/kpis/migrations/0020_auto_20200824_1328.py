# Generated by Django 3.0.7 on 2020-08-24 19:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kpis', '0019_kpi_beamline'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Beamline',
            new_name='Unit',
        ),
    ]
