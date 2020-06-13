from django.contrib import admin
from keypit.kpis import models


admin.site.register(models.Beamline)
admin.site.register(models.Department)
admin.site.register(models.KPI)
admin.site.register(models.KPIEntry)
admin.site.register(models.KPICategory)