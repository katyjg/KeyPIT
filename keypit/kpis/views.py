from django.views.generic import edit, detail, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from keypit.kpis import models


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
            departments = models.Department.objects.all()
            context.update(departments=departments)

        else:
            manager = self.request.user
            shipments = project.shipments.filter(
                Q(status__lt=models.Shipment.STATES.RETURNED)
                | Q(status=models.Shipment.STATES.RETURNED, date_returned__gt=one_year_ago)
            ).annotate(
                data_count=Count('containers__samples__datasets', distinct=True),
                report_count=Count('containers__samples__datasets__reports', distinct=True),
                sample_count=Count('containers__samples', distinct=True),
                group_count=Count('groups', distinct=True),
                container_count=Count('containers', distinct=True),
            ).order_by('status', '-date_shipped', '-created').prefetch_related('project')

            if settings.LIMS_USE_SCHEDULE:
                from mxlive.schedule.models import AccessType
                access_types = AccessType.objects.all()
                beamtimes = project.beamtime.filter(start__gte=one_year_ago, cancelled=False).with_duration().annotate(
                    upcoming=Case(When(start__gte=now, then=Value(True)), default=Value(False), output_field=BooleanField())
                ).annotate(
                    distance=Case(When(upcoming=True, then=F('start') - now), default=now - F('start'))
                ).order_by('-upcoming', 'distance')
                context.update(beamtimes=beamtimes, access_types=access_types)

            sessions = project.sessions.filter(
                created__gt=one_year_ago
            ).annotate(
                data_count=Count('datasets', distinct=True),
                report_count=Count('datasets__reports', distinct=True),
                last_record=Max('datasets__end_time'),
            ).order_by('last_record').with_duration().prefetch_related('project', 'beamline')[:7]

            context.update(shipments=shipments, sessions=sessions)
        return context