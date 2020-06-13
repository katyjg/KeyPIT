from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext as _

from model_utils import Choices


class Manager(AbstractUser):
    name = models.SlugField()


class Department(models.Model):
    """
    A Department object is a collection of one or more beamlines.
    """
    name = models.CharField(max_length=600)
    acronym = models.CharField(max_length=50)

    def __str__(self):
        return self.acronym


class Beamline(models.Model):
    """
    A Beamline object should be created for every unique facility that will be tracking KPIs,
    """
    name = models.CharField(max_length=600)
    acronym = models.CharField(max_length=50)
    department = models.ForeignKey(Department, blank=True, null=True, on_delete=models.SET_NULL, related_name="beamlines")

    def __str__(self):
        return self.acronym


class KPICategory(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=600, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "KPI Category"
        verbose_name_plural = "KPI Categories"


class KPI(models.Model):
    """
    A Key Performance Indicator to be tracked monthly for a beamline.
    """
    TYPE = Choices(
        (0, 'BAR', _('Bar Chart')),
        (1, 'LINE', _('Line Graph')),
        (2, 'SCATTER', _('Scatter Plot')),
    )
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=600)
    category = models.ForeignKey(KPICategory, blank=True, null=True, on_delete=models.SET_NULL, related_name="kpis")
    kind = models.IntegerField(choices=TYPE, default=TYPE.BAR)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Key Performance Indicator"


class KPIEntry(models.Model):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name="entries")
    beamline = models.ForeignKey(Beamline, on_delete=models.CASCADE, related_name="entries")
    month = models.DateField()
    value = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{}:{} | {}".format(self.beamline.acronym, self.month, self.kpi)

    class Meta:
        verbose_name = "KPI Entry"
        verbose_name_plural = "KPI Entries"
