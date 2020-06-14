from django.db.models import Avg, Sum
from django.utils import timezone

import calendar
from datetime import datetime
from memoize import memoize

from .models import KPIEntry, KPICategory, KPI

HOUR_SECONDS = 3600


#@memoize(timeout=HOUR_SECONDS)
def get_data_periods(period='year', **filters):
    field = 'month__{}'.format(period)
    return sorted(KPIEntry.objects.filter(**filters).values_list(field, flat=True).distinct())


def beamline_stats(beamline, period='month', **filters):
    field = 'month__{}'.format(period)
    filters['beamline'] = beamline

    entries = KPIEntry.objects.filter(**filters)
    categories = KPICategory.objects.filter(pk__in=entries.values_list('kpi__category__id', flat=True).distinct())

    periods = get_data_periods(period=period)
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
    summary_data = [[''] + period_names + ['Total / Average']]
    for cat in categories:
        content = []
        for kpi in KPI.objects.filter(category=cat, pk__in=entries.values_list('kpi__id', flat=True).distinct()):
            kpi_entries = kpi.entries.filter(**filters).order_by(field)

            if period == 'month':
                period_data = { p: kpi_entries.get(**{field: p}).value
                    for p in periods if kpi_entries.filter(**{field: p}).exists() }
                total = sum(period_data.values())
            else:
                if kpi.kind == kpi.TYPE.SUM:
                    period_data = { p: kpi_entries.filter(**{field: p}).aggregate(sum=Sum('value'))['sum']
                                    for p in periods }
                    total = sum(period_data.values())
                elif kpi.kind == kpi.TYPE.AVERAGE:
                    period_data = {p: round(kpi_entries.filter(**{field: p}).aggregate(avg=Avg('value'))['avg'], 1)
                                   for p in periods}
                    total = round(sum(period_data.values()) / len(period_data), 1)

            if kpi.kind == kpi.TYPE.SUM:
                period_trend = [sum(list(period_data.values())[:i + 1]) for i in range(len(periods))]
            else:
                period_trend = list(period_data.values())


            table_row = [[kpi.name] + [v for v in period_data.values()] + [total]]
            summary_data += table_row

            content.append({
                'title': kpi.name,
                'description': "<h4>{}</h4><p>{}</p>".format(kpi.name, kpi.description),
                'kind': 'table',
                'data': [[''] + period_names + [kpi.get_kind_display()]] + table_row,
                'header': 'column row',
                'style': 'col-12',
                'notes': "\n".join(
                    ["<strong>{}:</strong> {}".format(datetime.strftime(k.month, '%B'), k.comments)
                     for k in kpi_entries.exclude(comments="")]
                )
            })
            content.append({
                'title': kpi.name,
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'data': [
                        { period.title(): p, "Value": v }
                        for p, v in period_data.items()
                    ],
                },
                'style': 'col-12 col-md-6'
            })
            content.append({
                'title': "Trend Line",
                'kind': 'lineplot',
                'data': {
                    'x': [period.title()] + period_xvalues,
                    'y1': [['Value'] + period_trend],
                    'x-scale': x_scale,
                    'time-format': time_format
                },
                'style': 'col-12 col-md-6'
            })

        details.append({
            'title': cat.name,
            'description': cat.description,
            'style': 'row',
            'content': content
        })

    summary_table = [{
        'title': 'Summary',
        'style': 'row mb-4',
        'content': [{
            'kind': 'table',
            'header': 'column row',
            'data': summary_data,
            'style': 'col-12'
        }]
    }]
    stats = { 'details': summary_table + details }
    return stats
