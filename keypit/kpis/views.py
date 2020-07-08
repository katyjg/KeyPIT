from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Count, Subquery, OuterRef
from django.http import JsonResponse, HttpResponseRedirect
from django.template.defaultfilters import linebreaksbr
from django.urls import reverse_lazy
from django.views.generic import edit, detail, View

from itemlist.views import ItemListView
from datetime import datetime
import re

from keypit.kpis import models, forms, stats
from keypit.kpis.mixins import OwnerRequiredMixin, AdminRequiredMixin, ReportViewMixin, AsyncFormMixin, ListViewMixin, UserRoleMixin


def format_description(val, record):
    return linebreaksbr(val)


class LandingPage(UserRoleMixin, View):
    """
    Dispatch user to an appropriate view based on their roles.
    """

    def dispatch(self, request, *args, **kwargs):
        beamline = models.Beamline.objects.filter(
            acronym__icontains=re.search(r'\<beamline-staff:(.*?)\>', self.request.user.user_roles).group(1))
        if beamline.count() == 1:
            return HttpResponseRedirect(reverse_lazy('beamline-detail', kwargs={'pk': beamline.first().pk}))

        division = models.Department.objects.filter(
            acronym__icontains=re.search(r'\<employee:(.*?)\>', self.request.user.user_roles).group(1))
        if division.count() == 1:
            return HttpResponseRedirect(reverse_lazy('department-detail', kwargs={'pk': division.first().pk}))

        return HttpResponseRedirect(reverse_lazy('dashboard'))


class Dashboard(UserRoleMixin, detail.DetailView):
    """
    This is the "Dashboard" view.
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
        divisions = models.Department.objects.filter(division__isnull=True).annotate(beamline_count=Count('beamlines'), department_count=Count('departments'))
        departments = models.Department.objects.filter(division__isnull=False)
        context.update(divisions=divisions)
        context.update(departments=departments)
        context.update(beamlines=models.Beamline.objects.all())

        return context


class DepartmentList(UserRoleMixin, ListViewMixin, ItemListView):
    model = models.Department
    list_filters = ['division']
    list_columns = ['acronym', 'name', 'division']
    list_search = ['name', 'acronym']
    link_url = 'department-detail'
    add_url = 'new-department'
    link_data = False
    tool_template = 'kpis/components/kpi-list-tools.html'
    ordering = ['-division',]
    paginate_by = 25


class DepartmentDetail(UserRoleMixin, ReportViewMixin, detail.DetailView):
    model = models.Department
    template_name = "kpis/entries/department.html"

    def get_filters(self):
        filters = {'beamline__department': self.object}
        if self.object.is_division():
            filters = {'beamline__department__division': self.object}
        return filters


class DepartmentCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.DepartmentForm
    template_name = "modal/form.html"
    model = models.Department
    success_url = reverse_lazy('department-list')
    success_message = "Department has been created"


class DepartmentEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.DepartmentForm
    template_name = "modal/form.html"
    model = models.Department
    success_url = reverse_lazy('department-list')
    success_message = "Department has been updated"


class BeamlineList(UserRoleMixin, ListViewMixin, ItemListView):
    model = models.Beamline
    list_filters = ['department',]
    list_columns = ['acronym', 'name', 'department']
    list_search = ['name', 'acronym']
    link_url = 'beamline-detail'
    add_url = 'new-beamline'
    link_data = False
    tool_template = 'kpis/components/kpi-list-tools.html'
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


class BeamlineQuarter(BeamlineDetail):

    def get_filters(self):
        return {'beamline': self.object}


class BeamlineMonth(UserRoleMixin, detail.DetailView):
    model = models.Beamline
    template_name = "kpis/entries/beamline-month.html"

    def owner_roles(self):
        return ['{}:{}'.format(r, self.get_object().acronym.lower()) for r in
                ['beamline-admin', 'beamline-responsible', 'beamline-staff']]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.pop('year')
        month = self.kwargs.pop('month')

        entry = models.KPIEntry.objects.filter(month__year=year, month__month=month, beamline=self.object, kpi__pk=OuterRef('pk'))
        indicators = models.KPI.objects.filter(Q(department__in=self.object.departments()) | Q(beamline=self.object) | Q(department__isnull=True, beamline__isnull=True)).annotate(
            entry=Subquery(entry.values('pk')[:1]),
            value=Subquery(entry.values('value')[:1]),
            comments=Subquery(entry.values('comments')[:1])
        )

        entries = self.object.entries.filter(month__year=year, month__month=month).order_by('kpi__category__priority', 'kpi__priority')
        categories = models.KPICategory.objects.filter(pk__in=entries.values_list('kpi__category__id', flat=True).distinct())
        context['categories'] = {
            cat: entries.filter(kpi__category=cat) for cat in categories
        }
        if entries.filter(kpi__category__isnull=True).exists():
            context['categories']['Other'] = entries.filter(kpi__category__isnull=True)

        filters = {'month__year': year, 'beamline': self.object}
        context['years'] = stats.get_data_periods(period='year')
        context['months'] = stats.get_data_periods(period='month', **filters)
        context['quarters'] = stats.get_data_periods(period='quarter', **filters)
        context['year'] = year
        context['month'] = month

        categories = models.KPICategory.objects.filter(
            pk__in=indicators.values_list('category__id', flat=True).distinct())
        context['categories'] = {
            cat: indicators.filter(category=cat) for cat in categories
        }
        if indicators.filter(category__isnull=True).exists():
            context['categories']['Other'] = indicators.filter(category__isnull=True)

        return context


class BeamlineCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.BeamlineForm
    template_name = "modal/form.html"
    model = models.Beamline
    success_url = reverse_lazy('beamline-list')
    success_message = "Beamline has been created"


class BeamlineEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.BeamlineForm
    template_name = "modal/form.html"
    model = models.Beamline
    success_url = reverse_lazy('beamline-list')
    success_message = "Beamline has been updated"

    def owner_roles(self):
        return ['{}:{}'.format(r, self.get_object().acronym.lower())
                for r in ['beamline-admin', 'beamline-responsible', 'beamline-staff']]


class BeamlineCreateMonth(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.BeamlineMonthForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "Beamline report has been created"

    def owner_roles(self):
        bl = models.Beamline.objects.get(pk=self.kwargs.get('pk'))
        return ['{}:'.format(r) + bl.acronym.lower()
                for r in ['beamline-admin', 'beamline-responsible', 'beamline-staff']]

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
        for kpi in models.KPI.objects.filter(Q(department__in=self.beamline.departments()) | Q(department__isnull=True)):
            models.KPIEntry.objects.get_or_create(beamline=self.beamline, month=self.dt, kpi=kpi)

        return JsonResponse({'url': self.get_success_url()}, safe=False)


class BeamlineCreateThisMonth(BeamlineCreateMonth):

    def get_initial(self):
        initial = super().get_initial()
        initial['beamline'] = models.Beamline.objects.get(pk=self.kwargs.get('pk'))
        initial['year'] = self.kwargs.get('year')
        initial['month'] = self.kwargs.get('month')
        return initial


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


class KPIDetail(UserRoleMixin, ReportViewMixin, detail.DetailView):
    model = models.KPI
    template_name = "kpis/entries/kpi.html"

    def get_filters(self):
        return {'kpi': self.object}


class KPICreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.KPIForm
    template_name = "modal/form.html"
    model = models.KPI
    success_url = reverse_lazy('kpi-list')
    success_message = "KPI has been created"


class KPIEdit(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.KPIForm
    template_name = "modal/form.html"
    model = models.KPI
    success_url = reverse_lazy('kpi-list')
    success_message = "KPI has been updated"


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


class KPIEntryCreate(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.KPIEntryForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "KPI information has been updated"

    def get_initial(self):
        initial = super().get_initial()
        initial['beamline'] = models.Beamline.objects.filter(pk=self.request.GET.get('beamline')).first()
        initial['kpi'] = models.KPI.objects.filter(pk=self.request.GET.get('kpi', self.request.POST.get('kpi'))).first()
        initial['month'] = self.request.GET.get('month') and datetime.strptime('{}-1'.format(self.request.GET.get('month')), '%Y-%m-%d').date() or self.request.POST.get('month')
        return initial

    def get_success_url(self):
        success_url = reverse_lazy('beamline-month', kwargs={'pk': self.object.beamline.pk, 'year': self.object.month.year,
                                           'month': self.object.month.month})[:-1] + '#{}'.format(self.object.kpi.name)
        return success_url

    def owner_roles(self):
        beamline_pk = self.request.GET.get('beamline', self.request.POST.get('beamline'))
        beamline = models.Beamline.objects.filter(pk=beamline_pk).first()
        return ['{}:{}'.format(r, beamline.acronym.lower()) for r in
                ['beamline-admin', 'beamline-responsible', 'beamline-staff']]


class KPIEntryEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.KPIEntryForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "KPI information has been updated"

    def get_success_url(self):
        success_url = reverse_lazy('beamline-month', kwargs={'pk': self.object.beamline.pk, 'year': self.object.month.year,
                                           'month': self.object.month.month})[:-1] + '#{}'.format(self.object.kpi.name)
        return success_url

    def owner_roles(self):
        return ['{}:{}'.format(r, self.get_object().beamline.acronym.lower()) for r in
                ['beamline-admin', 'beamline-responsible', 'beamline-staff']]