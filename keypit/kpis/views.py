from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.template.defaultfilters import linebreaksbr
from django.urls import reverse_lazy
from django.views.generic import edit, detail, View


from itemlist.views import ItemListView
from datetime import datetime

from keypit.kpis import models, forms, stats
from keypit.kpis.mixins import OwnerRequiredMixin, AdminRequiredMixin, ReportViewMixin, AsyncFormMixin, ListViewMixin, UserRoleMixin


class Dashboard(LoginRequiredMixin, ReportViewMixin, detail.DetailView):
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

    def get_object(self, *args, **kwargs):
        # inject username in to kwargs if not already present
        if not self.kwargs.get('username'):
            self.kwargs['username'] = self.request.user.username
        return super(Dashboard, self).get_object(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        departments = models.Department.objects.all()
        context.update(departments=departments)

        return context


class DepartmentList(UserRoleMixin, ListViewMixin, ItemListView):
    model = models.Department
    list_filters = []
    list_columns = ['acronym', 'name']
    list_search = ['name', 'acronym']
    link_url = 'department-detail'
    link_data = False
    #ordering = ['status', '-modified']
    paginate_by = 25


class DepartmentDetail(UserRoleMixin, ReportViewMixin, detail.DetailView):
    model = models.Department
    template_name = "kpis/entries/department.html"

    def get_filters(self):
        return {'beamline__department': self.object}


class BeamlineList(UserRoleMixin, ListViewMixin, ItemListView):
    model = models.Beamline
    list_filters = ['department',]
    list_columns = ['id', 'name']
    list_search = ['name', 'acronym']
    link_url = 'beamline-detail'
    link_data = False
    ordering = ['department',]
    paginate_by = 25


class BeamlineDetail(UserRoleMixin, ReportViewMixin, detail.DetailView):
    model = models.Beamline
    template_name = "kpis/entries/beamline.html"

    def owner_roles(self):
        return ['{}:'.format(r) + self.get_object().acronym.lower() for r in
                ['beamline-admin', 'beamline-responsible', 'beamline-staff']]

    def get_filters(self):
        return {'beamline': self.object}


def format_description(val, record):
    return linebreaksbr(val)


class BeamlineMonth(UserRoleMixin, detail.DetailView):
    model = models.Beamline
    template_name = "kpis/entries/beamline-month.html"

    def owner_roles(self):
        return ['{}:'.format(r) + self.get_object().acronym.lower() for r in
                ['beamline-admin', 'beamline-responsible', 'beamline-staff']]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.pop('year')
        month = self.kwargs.pop('month')

        entries = self.object.entries.filter(month__year=year, month__month=month).order_by('kpi__category__priority', 'kpi__priority')
        categories = models.KPICategory.objects.filter(pk__in=entries.values_list('kpi__category__id', flat=True).distinct())
        context['categories'] = {
            cat: entries.filter(kpi__category=cat) for cat in categories
        }
        if entries.filter(kpi__category__isnull=True).exists():
            context['categories']['Other'] = entries.filter(kpi__category__isnull=True)

        filters = {'month__year': year}
        context['years'] = stats.get_data_periods(period='year')
        context['months'] = stats.get_data_periods(period='month', **filters)
        context['year'] = year
        context['month'] = month

        return context


class BeamlineMonthCreate(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.BeamlineMonthForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "Beamline report has been created"

    def owner_roles(self):
        bl = models.Beamline.objects.get(pk=self.kwargs.get('pk'))
        return ['{}:'.format(r) + bl.acronym.lower() for r in
                ['beamline-admin', 'beamline-responsible', 'beamline-staff']]

    def get_initial(self):
        initial = super().get_initial()
        initial['beamline'] = models.Beamline.objects.get(pk=self.kwargs.get('pk'))
        return initial

    def get_success_url(self):
        success_url = reverse_lazy('beamline-month', kwargs={'pk': self.beamline.pk, 'year': self.dt.year, 'month': self.dt.month})
        return success_url

    def form_valid(self, form):
        self.dt = datetime(form.cleaned_data['year'], form.cleaned_data['month'], 1).date()
        self.beamline = form.cleaned_data['beamline']
        for kpi in models.KPI.objects.all():
            models.KPIEntry.objects.get_or_create(beamline=self.beamline, month=self.dt, kpi=kpi)

        return JsonResponse({'url': self.get_success_url()}, safe=False)


class KPIList(UserRoleMixin, ListViewMixin, ItemListView):
    model = models.KPI
    list_filters = ['category', 'kind']
    list_columns = ['name', 'category', 'description', 'kind']
    list_transforms = {'description': format_description}
    list_search = ['name', 'description']
    link_url = 'kpi-detail'
    add_url = 'new-kpi'
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


class KPIDetail(UserRoleMixin, ReportViewMixin, detail.DetailView):
    model = models.KPI
    template_name = "kpis/entries/kpi.html"

    def get_filters(self):
        return {'kpi': self.object}


class KPIEntryCreate(BeamlineMonth):

    def get_context_data(self, **kwargs):
        beamline = models.Beamline.objects.get(pk=self.kwargs.get('pk'))
        month = datetime(self.kwargs.get('year'), self.kwargs.get('month'), 1).date()
        for kpi in models.KPI.objects.all():
            models.KPIEntry.objects.get_or_create(beamline=beamline, month=month, kpi=kpi)

        context = super().get_context_data(**kwargs)
        return context


class KPIEntryEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.KPIEntryForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "KPI information has been updated"

    def get_success_url(self):
        success_url = reverse_lazy('beamline-month', kwargs={'pk': self.object.beamline.pk, 'year': self.object.month.year,
                                           'month': self.object.month.month})
        return success_url


class KPICategoryList(UserRoleMixin, ListViewMixin, ItemListView):
    model = models.KPICategory
    list_filters = []
    list_columns = ['name', 'description', ]
    list_transforms = {'description': format_description}
    list_search = ['name', 'description']
    link_url = 'category-edit'
    link_attr = 'data-form-link'
    detail_target = '#modal-target'
    add_url = 'new-category'
    link_data = False
    tool_template = 'kpis/components/kpi-list-tools.html'
    ordering = ['priority']
    paginate_by = 25


class KPICategoryCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.KPICategoryForm
    template_name = "modal/form.html"
    model = models.KPICategory
    success_url = reverse_lazy('category-list')
    success_message = "Category has been created"


class KPICategoryEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.KPICategoryForm
    template_name = "modal/form.html"
    model = models.KPICategory
    success_url = reverse_lazy('category-list')
    success_message = "Category has been updated"




