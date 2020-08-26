from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Subquery, OuterRef
from django.http import HttpResponseRedirect, Http404
from django.template.defaultfilters import linebreaksbr
from django.urls import reverse_lazy
from django.views.generic import edit, detail, View

from itemlist.views import ItemListView
from datetime import datetime

from keypit.kpis import models, forms
from keypit.mixins.views import *


def format_description(val, record):
    return linebreaksbr(val)


class LandingPage(UserRoleMixin, View):
    """
    Dispatch user to an appropriate view based on their roles.
    """

    def dispatch(self, request, *args, **kwargs):
        try:
            unit = models.Unit.tree.filter(admin_roles__overlap=self.request.user.roles())
            #acronym__icontains=re.search(r'\<beamline-staff:(.*?)\>', self.request.user.user_roles).group(1))
            if unit.count() == 1:
                return HttpResponseRedirect(reverse_lazy('unit-detail', kwargs={'pk': unit.first().pk}))
        except:
            pass

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
        units = {
            kind.name: models.Unit.tree.filter(kind=kind) for kind in models.UnitType.objects.all()
        }
        context['units'] = {k: v for k, v in units.items() if v}
        return context


class UnitList(UserRoleMixin, ListViewMixin, ItemListView):
    model = models.Unit
    list_filters = ['parent', ]
    list_columns = ['acronym', 'name', 'kind__name', 'parent']
    list_search = ['name', 'acronym']
    link_url = 'unit-detail'
    add_url = 'new-unit'
    link_data = False
    tool_template = 'kpis/components/kpi-list-tools.html'
    ordering = ['parent', ]
    paginate_by = 25


class UnitDetail(UserRoleMixin, ReportViewMixin, detail.DetailView):
    model = models.Unit
    template_name = "kpis/entries/unit.html"

    def owner_roles(self):
        return self.get_object().owner_roles()

    def get_filters(self):
        return {'unit__in': [self.object] + list(self.object.descendants())}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        units = {
            kind.name: models.Unit.tree.filter(pk__in=self.object.children.values_list('pk', flat=True), kind=kind)
            for kind in models.UnitType.objects.all()
        }
        context['units'] = {k: v for k, v in units.items() if v}
        return context


class UnitReport(UserRoleMixin, detail.DetailView):
    model = models.Unit
    template_name = "kpis/entries/unit-report.html"

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().reporter():
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def owner_roles(self):
        return self.get_object().owner_roles()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.pop('year')
        month = self.kwargs.pop('month')

        entry = models.KPIEntry.objects.filter(
            month__year=year, month__month=month, unit=self.object, kpi__pk=OuterRef('pk'))
        indicators = models.KPI.objects.filter(
            units__pk__in=[self.object.pk] + list(self.object.ancestors().values_list('pk', flat=True))).annotate(
            entry=Subquery(entry.values('pk')[:1]),
            value=Subquery(entry.values('value')[:1]),
            comments=Subquery(entry.values('comments')[:1])
        )

        entries = self.object.entries.filter(
            month__year=year, month__month=month).order_by('kpi__category__priority', 'kpi__priority')
        categories = models.KPICategory.objects.filter(
            pk__in=entries.values_list('kpi__category__id', flat=True).distinct())
        context['categories'] = {
            cat: entries.filter(kpi__category=cat) for cat in categories
        }
        if entries.filter(kpi__category__isnull=True).exists():
            context['categories']['Other'] = entries.filter(kpi__category__isnull=True)

        filters = {'unit': self.object}
        context['years'] = stats.get_data_periods(period='year', **filters)
        if timezone.localtime().year not in context['years']:
            context['years'].append(timezone.localtime().year)

        filters['month__year'] = year
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


class UnitCreate(AdminRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.CreateView):
    form_class = forms.UnitForm
    template_name = "modal/form.html"
    model = models.Unit
    success_url = reverse_lazy('unit-list')
    success_message = "Unit has been created"


class UnitEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.UnitForm
    template_name = "modal/form.html"
    model = models.Unit
    success_url = reverse_lazy('unit-list')
    success_message = "Unit has been updated"

    def owner_roles(self):
        return self.get_object().owner_roles()


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
        initial['unit'] = models.Unit.tree.filter(pk=self.request.GET.get('unit')).first()
        initial['kpi'] = models.KPI.objects.filter(pk=self.request.GET.get('kpi', self.request.POST.get('kpi'))).first()
        initial['month'] = self.request.GET.get('month') and datetime.strptime(
            '{}-1'.format(self.request.GET.get('month')), '%Y-%m-%d').date() or self.request.POST.get('month')
        return initial

    def get_success_url(self):
        success_url = reverse_lazy('unit-report', kwargs={
            'pk': self.object.unit.pk, 'year': self.object.month.year,
            'month': self.object.month.month})[:-1] + '#{}'.format(self.object.kpi.name)
        return success_url

    def owner_roles(self):
        unit_pk = self.request.GET.get('unit', self.request.POST.get('unit'))
        unit = models.Unit.tree.filter(pk=unit_pk).first()
        return unit.owner_roles()


class KPIEntryEdit(OwnerRequiredMixin, SuccessMessageMixin, AsyncFormMixin, edit.UpdateView):
    form_class = forms.KPIEntryForm
    template_name = "modal/form.html"
    model = models.KPIEntry
    success_url = reverse_lazy('dashboard')
    success_message = "KPI information has been updated"

    def get_success_url(self):
        success_url = reverse_lazy('unit-report', kwargs={
            'pk': self.object.unit.pk, 'year': self.object.month.year,
            'month': self.object.month.month})[:-1] + '#{}'.format(self.object.kpi.name)
        return success_url

    def owner_roles(self):
        return self.get_object().unit.owner_roles()
