from django.utils import timezone

import calendar
from datetime import datetime
from memoize import memoize

from .models import KPIEntry, KPICategory, KPI

HOUR_SECONDS = 3600


#@memoize(timeout=HOUR_SECONDS)
def get_data_periods(period='year'):
    field = 'month__{}'.format(period)
    return sorted(KPIEntry.objects.values_list(field, flat=True).distinct())


def beamline_stats(beamline, period='month', **filters):
    field = 'month__{}'.format(period)
    periods = get_data_periods(period=period)
    entries = KPIEntry.objects.filter(beamline=beamline, **filters)
    categories = KPICategory.objects.filter(pk__in=entries.values_list('kpi__category__id', flat=True).distinct())

    period_names = periods

    if period == 'month':
        yr = timezone.now().year
        period_names = [calendar.month_abbr[per].title() for per in periods]
        period_xvalues = [datetime.strftime(datetime(yr, per, 1, 0, 0), '%c') for per in periods]
        time_format = '%b'
        x_scale = 'time'
    elif period == 'year':
        period_xvalues = [datetime.strftime(datetime(per, 1, 1, 0, 0), '%c') for per in periods]
        time_format = '%Y'
        x_scale = 'time'

    details = []
    for cat in categories:
        plots = []
        for kpi in KPI.objects.filter(category=cat, pk__in=entries.values_list('kpi__id', flat=True).distinct()):
            kpi_entries = kpi.entries.filter(beamline=beamline, **filters).order_by(field)
            kpi_values = list(kpi_entries.values_list('value', flat=True))
            plots.append({
                'title': kpi.name,
                'description': "<h4>{}</h4><p>{}</p>".format(kpi.name, kpi.description),
                'kind': 'table',
                'data': [[period.title()] + period_names] +
                        [[kpi.name] + [round(v) if v else 0 for v in kpi_values]],
                'header': 'column row',
                'style': 'col-12',
                'notes': "\n".join(["<strong>{}:</strong> {}".format(datetime.strftime(k.month, time_format), k.comments) for k in kpi_entries.filter(comments__isnull=True)])
            })
            plots.append({
                'title': kpi.name,
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'data': [
                        {period.title(): p, "Value": kpi.entries.filter(beamline=beamline).get(**{field: p}).value }
                        for p in periods
                    ],
                },
                'style': 'col-12 col-md-6'
            })
            plots.append({
                'title': kpi.name,
                'kind': 'lineplot',
                'data': {
                    'x': [period.title()] + period_xvalues,
                    'y1': [['Value'] + list(kpi.entries.filter(beamline=beamline, **filters).order_by(field).values_list('value', flat=True))],
                    'x-scale': x_scale,
                    'time-format': time_format
                },
                'style': 'col-12 col-md-6'
            })

        details.append({
            'title': cat.name,
            'description': cat.description,
            'style': 'row',
            'content': plots
        })

    stats = { 'details': details }
    return stats
