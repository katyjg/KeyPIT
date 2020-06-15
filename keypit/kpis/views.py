from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.template.defaultfilters import linebreaksbr
from django.urls import reverse_lazy
from django.views.generic import edit, detail, View


from itemlist.views import ItemListView
from datetime import datetime

from keypit.kpis import models, forms, stats
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
            kpis = models.KPI.objects.order_by('category__priority', 'priority').annotate(entries_count=Count('entries', distinct=True), beamlines_count=Count('entries__beamline', distinct=True))
            context.update(departments=departments, kpis=kpis)
        else:
            pass
        return context


class DepartmentList(ListViewMixin, ItemListView):
    model = models.Department
    list_filters = []
    list_columns = ['acronym', 'name']
    list_search = ['name', 'acronym']
    link_url = 'department-detail'
    link_data = False
    #ordering = ['status', '-modified']
    paginate_by = 25


class DepartmentDetail(LoginRequiredMixin, detail.DetailView):
    model = models.Department
    template_name = "kpis/entries/department.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = 'year'
        filters = {'beamline__department': self.object}
        context['years'] = stats.get_data_periods(period=period, **filters)

        if self.kwargs.get('year'):
            year = self.kwargs.pop('year')
            period = 'month'
            filters['month__year'] = year
            context['year'] = year
            context['months'] = stats.get_data_periods(period=period, **filters)
            if context['months']:
                if context['months'][-1] != 12: context['months'].append(context['months'][-1] + 1)
            else:
                context['months'] = [1]
            if year not in context['years']: context['years'].append(year)

            context['report'] = stats.beamline_stats(period=period, year=year, multi=True, **filters)
        else:
            context['report'] = stats.beamline_stats(period=period, **filters)
        return context


class BeamlineList(ListViewMixin, ItemListView):
    model = models.Beamline
    list_filters = ['department',]
    list_columns = ['id', 'name']
    list_search = ['name', 'acronym']
    link_url = 'beamline-detail'
    link_data = False
    ordering = ['department',]
    paginate_by = 25


class BeamlineDetail(LoginRequiredMixin, detail.DetailView):
    model = models.Beamline
    template_name = "kpis/entries/beamline.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = 'year'
        filters = {'beamline': self.object}
        context['years'] = stats.get_data_periods(period=period, **filters)

        if self.kwargs.get('year'):
            year = self.kwargs.pop('year')
            period = 'month'
            filters['month__year'] = year
            context['year'] = year
            context['months'] = stats.get_data_periods(period=period, **filters)
            if context['months']:
                if context['months'][-1] != 12: context['months'].append(context['months'][-1] + 1)
            else:
                context['months'] = [1]
            if year not in context['years']: context['years'].append(year)
            context['report'] = stats.beamline_stats(period=period, year=year, **filters)
        else:
            context['report'] = stats.beamline_stats(period=period, **filters)

        return context


def format_description(val, record):
    return linebreaksbr(val)


class BeamlineMonth(LoginRequiredMixin, detail.DetailView):
    model = models.Beamline
    template_name = "kpis/entries/beamline-month.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.pop('year')
        month = self.kwargs.pop('month')

        entries = self.object.entries.filter(month__year=year, month__month=month)
        categories = models.KPICategory.objects.filter(pk__in=entries.values_list('kpi__category__id', flat=True).distinct())
        context['categories'] = {
            cat: entries.filter(kpi__category=cat) for cat in categories
        }
        if entries.filter(kpi__category__isnull=True).exists():
            context['categories']['Other'] = entries.filter(kpi__category__isnull=True)

        filters = {'month__year': year}
        context['years'] = stats.get_data_periods(period='year')
        context['months'] = stats.get_data_periods(period='month', **filters)
        if context['months']:
            if context['months'][-1] == 12: context['years'].append(context['years'][-1] + 1)
            if context['months'][-1] != 12: context['months'].append(context['months'][-1] + 1)
        else:
            context['months'] = [1]
            context['years'].append(context['years'][-1] + 1)
        context['year'] = year
        context['month'] = month

        return context


class KPIList(ListViewMixin, ItemListView):
    model = models.KPI
    list_filters = ['category', 'kind']
    list_columns = ['name', 'category', 'description', 'kind']
    list_transforms = {'description': format_description}
    list_search = ['name', 'description']
    link_url = 'kpi-detail'
    link_data = False
    tool_template = 'kpis/components/kpi-list-tools.html'
    ordering = ['category__priority', 'priority']
    paginate_by = 25


class KPICreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.KPIForm
    template_name = "modal/form.html"
    model = models.KPI
    success_url = reverse_lazy('dashboard')
    success_message = "KPI has been created"


class KPIEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.KPIForm
    template_name = "modal/form.html"
    model = models.KPI
    success_url = reverse_lazy('dashboard')
    success_message = "KPI has been updated"


class KPIDetail(LoginRequiredMixin, detail.DetailView):
    model = models.KPI
    template_name = "kpis/entries/kpi.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = 'year'
        filters = {'kpi': self.object}
        context['years'] = stats.get_data_periods(period=period, **filters)

        if self.kwargs.get('year'):
            year = self.kwargs.pop('year')
            period = 'month'
            filters['month__year'] = year
            context['year'] = year
            context['months'] = stats.get_data_periods(period=period, **filters)
            if context['months']:
                if context['months'][-1] != 12: context['months'].append(context['months'][-1] + 1)
            else:
                context['months'] = [1]
            if year not in context['years']: context['years'].append(year)
            context['report'] = stats.beamline_stats(period=period, year=year, multi=True, **filters)
        else:
            context['report'] = stats.beamline_stats(period=period, **filters)

        return context


class KPIEntryCreate(BeamlineMonth):

    def get_context_data(self, **kwargs):
        beamline = models.Beamline.objects.get(pk=self.kwargs.get('pk'))
        month = datetime(self.kwargs.get('year'), self.kwargs.get('month'), 1).date()
        for kpi in models.KPI.objects.all():
            models.KPIEntry.objects.create(beamline=beamline, month=month, kpi=kpi)

        context = super().get_context_data(**kwargs)
        return context


class KPIeEntryCreate(SuccessMessageMixin, edit.CreateView):
    form_class = forms.BeamlineMonthForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "Beamline report has been created"

    def form_valid(self, form):
        month = datetime(form.cleaned_data['month'].year, form.cleaned_data['month'].month, 1).date()
        for kpi in models.KPI.objects.all():
            models.KPIEntry.objects.create(beamline=form.cleaned_data['beamline'], month=month, kpi=kpi)

        return HttpResponseRedirect(self.success_url)


class KPIEntryEdit(SuccessMessageMixin, edit.UpdateView):
    form_class = forms.KPIEntryForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "KPI information has been updated"


class KPIEntryDetail(SuccessMessageMixin, edit.UpdateView):
    form_class = forms.KPIEntryForm
    template_name = "form.html"
    model = models.KPI
    success_url = reverse_lazy('dashboard')
    success_message = "KPI has been created"

    def get_initial(self):
        initial = super().get_initial()
        initial['kpis'] = models.KPI.objects.all()
        return initial


