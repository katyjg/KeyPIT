from django.contrib.auth.mixins import LoginRequiredMixin


class ListViewMixin(LoginRequiredMixin):
    paginate_by = 25
    template_name = "kpis/list.html"
    link_data = False
    show_project = True

    def page_title(self):
        return self.model._meta.verbose_name_plural.title()