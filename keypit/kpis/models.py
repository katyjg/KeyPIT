from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from django_cas_ng.signals import cas_user_authenticated

from model_utils import Choices
import requests
import string

import logging
logger = logging.getLogger(__name__)


class Manager(AbstractUser):
    name = models.SlugField()
    user_roles = models.TextField(blank=True, null=True)

    def roles(self):
        return self.user_roles and self.user_roles.split(',') or []


@receiver(cas_user_authenticated)
def update_user_roleperms(sender, **kwargs):
    token = getattr(settings, 'PEOPLE_TOKEN', 'no token')
    auth_header = {'Authorization': 'Bearer {token}'.format(token=token)}
    if kwargs.get('created'):
        logger.info("New account {} created".format(kwargs.get('username')))

    r = requests.get('https://people.lightsource.ca/api/v2/people/{}/roles'.format(kwargs.get('username')), headers=auth_header)
    if r.status_code == 200:
        roles = [d.get('code') for d in r.json()]
        logger.info(roles)
        Manager.objects.filter(username=kwargs.get('username')).update(user_roles=','.join(['<{}>'.format(role) for role in roles]))


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
    description = models.CharField(verbose_name="Strategic Goal", max_length=600, blank=True)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def priority_display(self):
        number = list(KPICategory.objects.order_by('priority')).index(self)
        return "{}".format(number + 1)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
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
