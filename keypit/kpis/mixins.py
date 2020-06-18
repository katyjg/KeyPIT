from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse

from keypit.kpis import stats


class UserRoleMixin(LoginRequiredMixin):

    def owner_roles(self):
        return []

    def admin_roles(self):
        return ['science-manager:escience', 'science-manager:bioscience', 'science-manager:matscience']

    def employee_roles(self):
        return ['employee']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['admin'] = any(['<{}>'.format(r) in self.request.user.roles()
                                for r in self.admin_roles()]) or self.request.user.is_superuser
        context['owner'] = any(['<{}>'.format(r) in self.request.user.roles()
                                for r in self.owner_roles()]) or context['admin']
        context['employee'] = any(['<{}>'.format(r) in self.request.user.roles()
                                   for r in self.employee_roles()]) or context['owner']
        return context


class AdminRequiredMixin(UserRoleMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is a superuser.
    Can be used with any View.
    """

    def test_func(self):
        return any(['<{}>'.format(r) in self.request.user.roles()
                                for r in self.admin_roles()]) or self.request.user.is_superuser


class OwnerRequiredMixin(UserRoleMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is an employee
    Can be used with any View.
    """

    def test_func(self):
        return any(['<{}>'.format(r) in self.request.user.roles()
                                for r in self.owner_roles()])


class EmployeeRequiredMixin(UserRoleMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is an employee
    Can be used with any View.
    """

    def test_func(self):
        return any(['<{}>'.format(r) in self.request.user.roles()
                                for r in self.employee_roles()])


class ReportViewMixin(object):

    def get_filters(self):
        return {}

    def get_context_data(self, **kwargs):
        report_ctx = super().get_context_data(**kwargs)

        year = self.kwargs.get('year')
        filters = self.get_filters()

        report_ctx['years'] = stats.get_data_periods(period='year', **filters)

        if year:
            period = 'month'
            filters.update({'month__year': year})
            report_ctx['year'] = year
            report_ctx['months'] = stats.get_data_periods(period=period, **filters)
            report_ctx['report'] = stats.beamline_stats(period=period, year=year, **filters)
        else:
            report_ctx['report'] = stats.beamline_stats(period='year', **filters)

        return report_ctx

class ListViewMixin(LoginRequiredMixin):
    paginate_by = 25
    template_name = "kpis/list.html"
    link_data = False
    show_project = True

    def page_title(self):
        return self.model._meta.verbose_name_plural.title()


class AsyncFormMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    modal_response = False

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.is_ajax():
            data = {
                'modal': self.modal_response,
                'url': self.get_success_url(),
            }
            return JsonResponse(data, safe=False)
        else:
            return response