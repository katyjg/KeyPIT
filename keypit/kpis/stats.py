from django.db.models import Avg, Sum, Value, TextField, Func
from django.db.models.functions import Concat
from django.template.defaultfilters import linebreaksbr, mark_safe

import calendar
from copy import deepcopy
from datetime import datetime

from .models import KPIEntry, KPI, KPIFamily

HOUR_SECONDS = 3600
COLORS = ["#006eb6", "#990099", "#512D6D", "#41864A", "#F0AD4E"]


def get_data_periods(period='year', **filters):
    field = 'month__{}'.format(period)
    return sorted(KPIEntry.objects.filter(**filters).values_list(field, flat=True).distinct())


class MonthCast(Func):
   """
   Coerce an expression to a new field type.
   """
   function = 'TO_CHAR'
   template = '%(function)s(%(expressions)s, \'Month YYYY\')'


def unit_stats(period='month', year=None, **filters):
    field = 'month__{}'.format(period)
    entries = KPIEntry.objects.filter(**filters)
    units = len(entries.values_list('unit', flat=True).distinct()) > 1

    if entries.count():
        categories = entries.values('kpi__category', 'kpi__category__name', 'kpi__category__description').distinct().order_by('kpi__category__priority')

        periods = get_data_periods(period=period, **filters)
        period_names = period == 'month' and [calendar.month_abbr[per].title() for per in periods] \
                       or period == 'quarter' and ['Q{}'.format(per) for per in periods] \
                       or periods
        time_format = period == 'month' and '%b' or '%Y'

        details = []
        kpi_data = {}
        summary_data = [[''] + period_names + ['Total / Avg']]
        for cat in categories:
            content = []
            for kpi in KPI.objects.filter(category__id=cat['kpi__category'], pk__in=entries.values_list('kpi__id', flat=True).distinct()).order_by('priority'):
                content += [{
                    'title': kpi.name,
                    'description': "<h4>{}. {}</h4><p>{}</p>".format(kpi.priority_display(), kpi.name, linebreaksbr(kpi.description)),
                    'style': 'col-12 text-condensed px-5'
                }]

                kpi_filters = deepcopy(filters)
                kpi_filters.update({'kpi': kpi})
                kpi_entries = kpi.entries.filter(**kpi_filters)

                kpi_comment_entries = kpi_entries.exclude(comments="").exclude(comments__isnull=True).order_by('-month', 'unit__parent', 'unit').annotate(
                    str_month=MonthCast('month', output_field=TextField())).annotate(
                    fmt_comments=Concat(Value('<strong>'), units and 'unit__acronym' or Value(''), Value(' '), 'str_month', Value('</strong><br/>'),
                                        'comments', output_field=TextField())).values_list('fmt_comments', flat=True)

                kpi_comments = '<br/><br/>'.join(kpi_comment_entries)
                kpi_comments = linebreaksbr(mark_safe(kpi_comments))

                if kpi.kind != kpi.TYPE.TEXT:
                    # Add plots to the report
                    kpi_filters.update({'value__isnull': False})
                    kpi_periods = get_data_periods(period=period, **kpi_filters)
                    kpi_entries.filter(**kpi_filters).order_by(field)
                    total = '-'
                    period_trend = {}
                    if kpi.kind == kpi.TYPE.SUM:
                        period_data = { p: kpi_entries.filter(**{field: p}).aggregate(sum=Sum('value'))['sum']
                                        for p in kpi_periods }
                        period_trend = { p: sum(list(period_data.values())[:i + 1]) for i, p in enumerate(kpi_periods)}
                        if period_data:
                            total = sum(list(period_data.values()))
                    elif kpi.kind == kpi.TYPE.AVERAGE:
                        period_data = {p: kpi_entries.filter(**{field: p}).exclude(value__isnull=True).aggregate(avg=Avg('value'))['avg']
                                       for p in kpi_periods}
                        period_data = {k: round(v, 1) or v for k, v in period_data.items()}
                        if period_data:
                            total = round(sum(period_data.values()) / len(period_data), 1)
                    summary_data += [[kpi.name] + [period_data.get(p, '-') for p in periods] + [total]]

                    if period_data:
                        kpi_data[kpi.pk] = { period == 'year' and p or datetime.strftime(datetime(year, p, 1, 0, 0), '%b'): v for p, v in period_data.items() }
                        content += [{
                            'style': 'col-lg-2 d-lg-block'
                        }, {
                            'title': kpi.name,
                            'kind': 'columnchart',
                            'data': {
                                'colors': COLORS,
                                'x-label': period.title(),
                                'data': period_trend and [
                                    { period.title(): p, "Value": v, "Total": period_trend.get(p, 0) }
                                    for p, v in kpi_data[kpi.pk].items()
                                ] or [
                                    { period.title(): p, "Value": v }
                                    for p, v in kpi_data[kpi.pk].items()
                                ],
                                'line': period_trend and "Total" or "",
                            },
                            'style': 'col-12 col-lg-8 px-5'
                        }, {
                            'style': 'col-lg-2 d-lg-block'
                        }]
                    else:
                        content += [{
                            'notes': "No data available",
                            'style': 'col-12 px-5'
                        }]

                if kpi_comments or kpi.kind == kpi.TYPE.TEXT:
                    # Add comments to the report
                    content += [{
                        'notes': kpi_comments or 'No data available',
                        'style': 'col-12 px-5'
                    }]

            details.append({
                'title': cat['kpi__category__name'],
                'style': 'row',
                'content': [cat['kpi__category__description'] and {
                    'description': "<span class='text-bold text-large text-condensed'>STRATEGIC GOAL:</span>\n{}".format(
                        cat['kpi__category__description']),
                    'style': 'col-12 jumbotron pt-4 pb-2 text-muted'
                }] + content
            })

        family_content = []
        for family in KPIFamily.objects.filter(kpis__pk__in=entries.values_list('kpi__pk', flat=True)).distinct():
            family_kpis = family.kpis.filter(pk__in=kpi_data.keys())
            if family_kpis.count() > 1:
                periods = []
                for pk in family_kpis.values_list('pk', flat=True):
                    for k in kpi_data[pk]:
                        if k not in periods: periods.append(k)
                if period == 'year':
                    periods = sorted(periods)
                elif period == 'month':
                    periods = sorted(periods, key=lambda x: datetime.strptime(x, '%b').month)
                family_data = []
                for per in periods:
                    family_data.append({ period.title(): per })
                for f in family_data:
                    for kpi in family_kpis:
                        f[kpi.name] = kpi_data[kpi.pk].get(f[period.title()], 0)
                family_content.append({
                    'title': family.name,
                    'kind': 'columnchart',
                    'data': {
                        'colors': COLORS,
                        'x-label': period.title(),
                        'data': family_data,
                        'stack': family.kind == family.TYPE.CUMULATIVE and [[kpi.name for kpi in family_kpis]] or [],
                    },
                    'style': 'col-12 col-md-6 px-5'
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
        for plot in family_content:
            summary_table[0]['content'].append(plot)
        stats = { 'details': summary_table + details }
    else:
        stats = { 'details': [{
            'title': 'No information',
            'style': 'row mb-4'
        }]}
    return stats
