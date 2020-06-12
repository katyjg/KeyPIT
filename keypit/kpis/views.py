from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.views.generic import edit, detail, View

from itemlist.views import ItemListView

from keypit.kpis import models
from keypit.kpis.mixins import *


class Dashboard(UserPassesTestMixin, detail.DetailView):
    """
    This is the "Dashboard" view. Basic information about the Project is displayed:

    :For superusers, direct to staff.html, with context:
       - shipments: Any Shipments that are Sent or On-site
       - automounters: Any active Dewar objects (Beamline/Automounter)

    :For Users, direct to project.html, with context:
       - shipments: All Shipments that are Draft, Sent, or On-site, plus Returned shipments to bring the total displayed up to seven.
       - sessions: Any recent Session from any beamline
    """
    model = models.Manager
    template_name = "kpis/dashboard.html"
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        # Allow access to admin or owner
        return self.request.user.is_superuser or self.get_object() == self.request.user

    def get_object(self, *args, **kwargs):
        # inject username in to kwargs if not already present
        if not self.kwargs.get('username'):
            self.kwargs['username'] = self.request.user.username
        return super(Dashboard, self).get_object(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        if self.request.user.is_superuser:
            departments = models.Department.objects.annotate(beamline_count=Count('beamlines', distinct=True))
            kpis = models.KPI.objects.annotate(entries_count=Count('entries', distinct=True), beamlines_count=Count('entries__beamline', distinct=True))
            context.update(departments=departments, kpis=kpis)

        else:
            pass
        return context


class DepartmentList(ListViewMixin, ItemListView):
    model = models.Department
    list_filters = []
    list_columns = ['id', 'name']
    list_search = ['name', 'acronym']
    #link_url = 'department-detail'
    link_data = False
    #ordering = ['status', '-modified']
    paginate_by = 25


class BeamlineList(ListViewMixin, ItemListView):
    model = models.Beamline
    list_filters = ['department',]
    list_columns = ['id', 'name']
    list_search = ['name', 'acronym']
    #link_url = 'department-detail'
    link_data = False
    #ordering = ['status', '-modified']
    paginate_by = 25


class KPIList(ListViewMixin, ItemListView):
    model = models.KPI
    list_filters = []
    list_columns = ['id', 'name', 'description']
    list_search = ['name', 'description']
    #link_url = 'department-detail'
    link_data = False
    #ordering = ['status', '-modified']
    paginate_by = 25