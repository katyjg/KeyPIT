# Generated by Django 3.0.7 on 2020-06-16 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kpis', '0013_auto_20200615_1516'),
    ]

    operations = [
        migrations.AddField(
            model_name='beamline',
            name='beamlines',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
