from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.utils import timezone

from keypit.kpis import stats


class UserRoleMixin(LoginRequiredMixin):

    def admin_roles(self):
        return []

    def owner_roles(self):
        return []

    def employee_roles(self):
        return ['employee']

    def is_admin(self):
        return any(['{}'.format(r) in self.request.user.roles() for r in
                    self.admin_roles()]) or self.request.user.is_superuser

    def is_owner(self):
        return any(['{}'.format(r) in self.request.user.roles() for r in self.owner_roles()]) or self.is_admin()

    def is_employee(self):
        return any(['{}'.format(r) in self.request.user.roles() for r in self.employee_roles()]) or self.is_owner()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['admin'] = self.is_admin()
        context['owner'] = self.is_owner()
        context['employee'] = self.is_employee()
        return context


class AdminRequiredMixin(UserRoleMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is a superuser.
    Can be used with any View.
    """

    def test_func(self):
        return self.is_admin()


class OwnerRequiredMixin(UserRoleMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is an owner as defined by owner_roles
    Can be used with any View.
    """

    def test_func(self):
        return self.is_owner()


class EmployeeRequiredMixin(UserRoleMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is an employee
    Can be used with any View.
    """

    def test_func(self):
        return self.is_employee()


class ReportViewMixin(object):

    def get_filters(self):
        return {}

    def get_context_data(self, **kwargs):
        report_ctx = super().get_context_data(**kwargs)

        year = self.kwargs.get('year')
        period = self.kwargs.get('period') or 'year'
        filters = self.get_filters()

        report_ctx['years'] = stats.get_data_periods(period='year', **filters)
        if timezone.localtime().year not in report_ctx['years']:
            report_ctx['years'].append(timezone.localtime().year)

        if year:
            filters.update({'month__year': year})
            report_ctx['year'] = year
            for per in ['month']:
                report_ctx['{}s'.format(per)] = stats.get_data_periods(period=per, **filters)
            if self.kwargs.get('quarter'):
                period = 'month'
                report_ctx['quarter'] = self.kwargs.get('quarter')
                filters.update({'month__quarter': self.kwargs.get('quarter')})
            report_ctx['report'] = stats.unit_stats(period=period, year=year, **filters)
        else:
            report_ctx['report'] = stats.unit_stats(period='year', **filters)

        report_ctx['period'] = period

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
