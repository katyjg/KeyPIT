# Generated by Django 3.0.7 on 2020-06-17 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kpis', '0015_auto_20200617_1419'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='user_roles',
            field=models.TextField(blank=True, null=True),
        ),
    ]
