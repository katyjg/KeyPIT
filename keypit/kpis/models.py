from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from django_cas_ng.signals import cas_user_authenticated

from keypit.mixins.models import TreeModel
from model_utils import Choices
import requests
import string

import logging
logger = logging.getLogger(__name__)

ADMIN_USERS = getattr(settings, 'ADMIN_USERS', [])
ADMIN_ROLES = getattr(settings, 'ADMIN_ROLES', [])
PEOPLE_API = getattr(settings, 'PEOPLE_API', 'https://people.lightsource.ca/api/v2/people/')
PEOPLE_TOKEN = getattr(settings, 'PEOPLE_TOKEN', 'no token')


class Manager(AbstractUser):
    name = models.SlugField()
    user_roles = models.TextField(blank=True, null=True)

    def roles(self):
        return self.user_roles and self.user_roles.replace('<', '').replace('>', '').split(',') or []


@receiver(cas_user_authenticated)
def update_user_roleperms(sender, **kwargs):
    auth_header = {'Authorization': 'Bearer {token}'.format(token=PEOPLE_TOKEN)}
    user = Manager.objects.get(username=kwargs.get('username'))
    if kwargs.get('created'):
        logger.info("New account {} created".format(user.username))

    r = requests.get('{api}{username}/roles'.format(api=PEOPLE_API, username=user.username), headers=auth_header)
    if r.status_code == 200:
        roles = [d.get('code') for d in r.json()]
        logger.info('User roles: {}'.format(roles))
        user.user_roles = ','.join(['{}'.format(role) for role in roles])
        user.save()

    if user.username in ADMIN_USERS or any(['{}'.format(r) in user.roles() for r in ADMIN_ROLES]):
        logger.info('User {} is superuser'.format(user.username))
        user.is_superuser = True
        user.is_staff = True
        user.save()


class UnitType(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    description = models.TextField(blank=True)
    reporter = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Unit(TreeModel):
    """
    A Unit object should be created for every unique facility that will be tracking KPIs,
    """
    name = models.CharField(max_length=600)
    acronym = models.CharField(max_length=50)
    kind = models.ForeignKey(UnitType, on_delete=models.SET_NULL, null=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children', verbose_name=_('Parent'), on_delete=models.SET_NULL
    )
    acronyms = models.CharField(_('USO Acronyms'), max_length=200, blank=True, null=True)
    admin_roles = ArrayField(models.CharField(max_length=200), blank=True, default=list)

    def __str__(self):
        return self.acronym

    def beamline_acronyms(self):
        return self.acronyms and [ba.strip() for ba in self.acronyms.split(',')] or [self.acronym]

    def owner_roles(self):
        return self.admin_roles

    def reporter(self):
        return self.kind.reporter

    def reporting_subunits(self):
        return [u for u in self.descendants() if u.reporter()]

    def indicators(self):
        return KPI.objects.filter(units__pk__in=[self.pk] + list(self.ancestors().values_list('pk', flat=True)))

    def inherited(self):
        return self.indicators().exclude(units__pk=self.pk)

    def dendrogram(self):
        return {
            "name": self.acronym,
            "pk": self.pk,
            "children": [ child.dendrogram() for child in self.children.all() ]
         }


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
        ordering = ['priority', ]


class KPI(models.Model):
    """
    A Key Performance Indicator to be tracked monthly for a beamline or other organizational unit.
    """
    TYPE = Choices(
        (0, 'AVERAGE', _('Average')),
        (1, 'SUM', _('Total')),
        (2, 'TEXT', _('Text Only')),
    )
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=600)
    category = models.ForeignKey(KPICategory, blank=True, null=True, on_delete=models.SET_NULL, related_name='kpis')
    units = models.ManyToManyField(Unit, blank=True)
    kind = models.IntegerField(choices=TYPE, default=TYPE.SUM)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def priority_display(self):
        letter = list(self.category.kpis.order_by('priority')).index(self)
        return "{}{}".format(self.category.priority_display(), string.ascii_lowercase[letter])

    def reporting_units(self):
        units =  set(list(self.units.all()) + [i for sub in [u.descendants() for u in self.units.all()] for i in sub])
        return [u for u in units if u.kind.reporter]

    class Meta:
        verbose_name = "Key Performance Indicator"
        ordering = ['category__priority', 'priority', ]


class KPIFamily(models.Model):
    TYPE = Choices(
        (0, 'RELATED', _('Related')),
        (1, 'CUMULATIVE', _('Cumulative')),
    )
    name = models.CharField(max_length=250)
    kpis = models.ManyToManyField(KPI)
    kind = models.IntegerField(choices=TYPE, default=TYPE.RELATED)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "KPI Family"
        verbose_name_plural = "KPI Families"


class KPIEntry(models.Model):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name="entries")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="entries")
    month = models.DateField()
    value = models.IntegerField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{}:{} | {}".format(self.unit.acronym, self.month, self.kpi)

    class Meta:
        verbose_name = "KPI Entry"
        verbose_name_plural = "KPI Entries"
        unique_together = ['kpi', 'unit', 'month']
