from django.db.models import Avg, Sum
from django.template.defaultfilters import linebreaksbr
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


def beamline_stats(period='month', year=timezone.now().year, **filters):
    field = 'month__{}'.format(period)
    entries = KPIEntry.objects.filter(**filters)

    if entries:
        #categories = KPICategory.objects.filter(pk__in=entries.values_list('kpi__category__id', flat=True).distinct())
        categories = entries.values('kpi__category', 'kpi__category__name', 'kpi__category__description').distinct().order_by('kpi__category__priority')
        beamlines = entries.values('beamline').distinct().count() > 1

        periods = get_data_periods(period=period)
        period_names = period == 'month' and [calendar.month_abbr[per].title() for per in periods] or periods
        time_format = period == 'month' and '%b' or '%Y'

        details = []
        summary_data = [[''] + period_names + ['Total / Avg']]
        for cat in categories:
            content = []
            for kpi in KPI.objects.filter(category__id=cat['kpi__category'], pk__in=entries.values_list('kpi__id', flat=True).distinct()).order_by('priority'):
                kpi_entries = kpi.entries.filter(**filters).order_by(field)
                kpi_periods = get_data_periods(period=period, **{'kpi': kpi})
                kpi_period_names = period == 'month' and [calendar.month_abbr[per].title() for per in kpi_periods] or kpi_periods
                kpi_period_xvalues = [datetime.strftime(datetime(period == 'month' and year or per, period == 'month' and per or 1, 1, 0, 0), '%c') for per in kpi_periods]
                kpi_comments = period == 'month' and '<br/><br/>'.join(
                        [ '<strong>{} {}:</strong><br/>{}'.format(beamlines and k.beamline.acronym or '', datetime.strftime(k.month, '%B'), k.comments)
                            for k in kpi_entries.order_by('-month').exclude(comments="").exclude(comments__isnull=True) ]
                    ) or ''
                if kpi.kind == kpi.TYPE.TEXT:
                    content.append({
                        'title': kpi.name,
                        'description': '<h4>{}. {}</h4><p>{}</p>'.format(kpi.priority_display(), kpi.name,
                                                                         linebreaksbr(kpi.description)),
                        'style': 'col-12',
                        'notes': kpi_comments
                    })
                else:
                    if kpi.kind == kpi.TYPE.SUM:
                        period_data = { p: kpi_entries.filter(**{field: p}).aggregate(sum=Sum('value'))['sum'] or 0
                                        for p in kpi_periods }
                        period_trend = [sum(list(period_data.values())[:i + 1]) for i in range(len(kpi_periods))]
                        total = sum(period_data.values())
                    elif kpi.kind == kpi.TYPE.AVERAGE:
                        period_data = {p: kpi_entries.filter(**{field: p}).aggregate(avg=Avg('value'))['avg'] or 0
                                       for p in kpi_periods}
                        period_data = {k: round(v, 1) for k, v in period_data.items()}
                        period_trend = list(period_data.values())
                        total = round(sum(period_data.values()) / len(period_data), 1)

                    table_row = [[kpi.name] + [period_data.get(p, '-') for p in kpi_periods] + [total]]
                    summary_data += [[kpi.name] + [period_data.get(p, '-') for p in periods] + [total]]

                    content += [{
                        'title': kpi.name,
                        'description': "<h4>{}. {}</h4><p>{}</p>".format(kpi.priority_display(), kpi.name,
                                                                         linebreaksbr(kpi.description)),
                        'style': 'col-12 text-condensed'
                    }, {
                        'kind': 'table',
                        'data': [[""] + kpi_period_names + [kpi.get_kind_display()]] + [[""] + table_row[0][1:]],
                        'header': 'row',
                        'style': 'col-12',
                        'notes': kpi_comments
                    }, {
                        'title': kpi.name,
                        'kind': 'columnchart',
                        'data': {
                            'x-label': period.title(),
                            'data': [
                                { period.title(): period == 'year' and p or datetime.strftime(datetime(year, p, 1, 0, 0), '%b'), "Value": v }
                                for p, v in period_data.items()
                            ],
                        },
                        'style': 'col-12 col-md-6'
                    }, {
                        'title': "Trend Line",
                        'kind': 'lineplot',
                        'data': {
                            'x': [period.title()] + kpi_period_xvalues,
                            'y1': [['Value'] + period_trend],
                            'x-scale': 'time',
                            'time-format': time_format
                        },
                        'style': 'col-12 col-md-6'
                    }]

            details.append({
                'title': cat['kpi__category__name'],
                'description': cat['kpi__category__description'],
                'style': 'row jumbotron pb-2 pt-4',
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
    else:
        stats = { 'details': [{
            'title': 'No information',
            'style': 'row mb-4'
        }]}
    return stats
