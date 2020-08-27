from django.contrib import admin
from keypit.kpis import models

admin.site.register(models.Manager)
admin.site.register(models.UnitType)
admin.site.register(models.Unit)
admin.site.register(models.KPI)
admin.site.register(models.KPIEntry)
admin.site.register(models.KPIFamily)
admin.site.register(models.KPICategory)