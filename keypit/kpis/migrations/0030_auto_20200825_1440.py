# Generated by Django 3.0.7 on 2020-08-25 20:40

from django.db import migrations


def update_roles(apps, schema_editor):

    Manager = apps.get_model('kpis', 'Manager')
    Unit = apps.get_model('kpis', 'Unit')
    db_alias = schema_editor.connection.alias

    for person in Manager.objects.using(db_alias).all():
        person.user_roles = person.user_roles and person.user_roles.replace('<','').replace('>','') or ""
        person.save()

    for unit in Unit.tree.using(db_alias).filter(kind__name="Beamline"):
        unit.admin_roles = ["{}:{}".format(r, unit.acronym.lower()) for r in ["beamline-admin", "beamline-responsible", "beamline-staff"]]
        unit.save()


class Migration(migrations.Migration):

    dependencies = [
        ('kpis', '0029_unit_admin_roles'),
    ]

    operations = [
        migrations.RunPython(update_roles),
    ]
