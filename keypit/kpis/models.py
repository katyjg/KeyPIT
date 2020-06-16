from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext as _

from model_utils import Choices
import string


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
    beamlines = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.acronym

    def beamline_acronyms(self):
        return self.beamlines and [ba.strip() for ba in self.beamlines.split(',')] or [self.acronym]


class KPICategory(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=600, blank=True)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def priority_display(self):
        number = list(KPICategory.objects.order_by('priority')).index(self)
        return "{}".format(number + 1)

    class Meta:
        verbose_name = "KPI Category"
        verbose_name_plural = "KPI Categories"
        ordering = ['priority',]


class KPI(models.Model):
    """
    A Key Performance Indicator to be tracked monthly for a beamline.
    """
    TYPE = Choices(
        (0, 'AVERAGE', _('Average')),
        (1, 'SUM', _('Total')),
        (2, 'TEXT', _('Text Only')),
    )
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=600)
    category = models.ForeignKey(KPICategory, blank=True, null=True, on_delete=models.SET_NULL, related_name="kpis")
    kind = models.IntegerField(choices=TYPE, default=TYPE.SUM)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def priority_display(self):
        letter = list(self.category.kpis.order_by('priority')).index(self)
        return "{}{}".format(self.category.priority_display(), string.ascii_lowercase[letter])

    class Meta:
        verbose_name = "Key Performance Indicator"
        ordering = ['category__priority', 'priority',]


class KPIEntry(models.Model):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name="entries")
    beamline = models.ForeignKey(Beamline, on_delete=models.CASCADE, related_name="entries")
    month = models.DateField()
    value = models.IntegerField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{}:{} | {}".format(self.beamline.acronym, self.month, self.kpi)

    class Meta:
        verbose_name = "KPI Entry"
        verbose_name_plural = "KPI Entries"
        unique_together = ['kpi', 'beamline', 'month']
