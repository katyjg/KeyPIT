from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from datetime import datetime, timedelta
import pytz
import requests

from keypit.kpis.models import Beamline, KPI, KPIEntry

USO_API = getattr(settings, 'USO_API', 'https://user.lightsource.ca/api/v1/')

BEAMLINE_AVAILABILITY = 7
TOTAL_NORMAL_SHIFTS = 8
TOTAL_SHIFTS_USED = 9
PEER_REVIEWED_ARTICLES = 5
THESES = 14

def format_localtime(dt):
    return datetime.strftime(timezone.localtime(pytz.utc.localize(dt)), '%Y-%m-%dT%H')


class Command(BaseCommand):
    help = """Fetches Publications and Scheduling KPIs information from the CLS USO
                - provide an optional --date in the format yyyy-mm-dd"""

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str)

    def handle(self, *args, **options):
        strdt = options.get('date', None)
        dt = strdt and datetime.strptime(strdt, '%Y-%m-%d') or timezone.now() - timedelta(days=1)
        start = timezone.datetime(dt.year, dt.month, 1)
        end = timezone.datetime(dt.year, dt.month + 1, 1)
        qstart = datetime.strftime(start, '%Y-%m-%d')
        qend = datetime.strftime(end, '%Y-%m-%d')

        # Import Modes
        n_shifts = []
        url = "{}schedule/modes/?start={}&end={}".format(USO_API, qstart, qend)
        r = requests.get(url)
        if r.status_code == 200:
            modes = [s for s in r.json() if s['kind'] == 'N' and not s['cancelled']]
            for mode in modes:
                st = datetime.strptime(mode['start'], '%Y-%m-%dT%H:%M:%SZ')
                while st < datetime.strptime(mode['end'], '%Y-%m-%dT%H:%M:%SZ'):
                    if st >= start and st < end: n_shifts.append(format_localtime(st))
                    st += timedelta(hours=8)
        n_shifts = set(n_shifts)

        for bl in Beamline.objects.all():
            KPIEntry.objects.filter(beamline=bl, month=start, kpi__id=TOTAL_NORMAL_SHIFTS).update(value=len(n_shifts))

            # Import Facility Schedule(s)
            url = "{}schedule/beamtime/{}/?start={}&end={}".format(USO_API, bl.acronym, qstart, qend)
            r = requests.get(url)
            if r.status_code == 200:
                visits = [s for s in r.json() if not s['cancelled']]
                shifts = []
                for visit in visits:
                    st = datetime.strptime(visit['start'], '%Y-%m-%dT%H:%M:%SZ')
                    while st < datetime.strptime(visit['end'], '%Y-%m-%dT%H:%M:%SZ'):
                        shifts.append(format_localtime(st))
                        st += timedelta(hours=8)
            else:
                print("Schedule not found for {}".format(bl.acronym))
            used_shifts = len(n_shifts.intersection(set(shifts)))
            percent_used = n_shifts and 100. * used_shifts / len(n_shifts) or 0
            KPIEntry.objects.filter(beamline=bl, month=start.date(), kpi__id=TOTAL_SHIFTS_USED).update(value=used_shifts)
            KPIEntry.objects.filter(beamline=bl, month=start.date(), kpi__id=BEAMLINE_AVAILABILITY).update(value=percent_used)

            # Import Facility Publications
            url = "{}publications/article/{}/".format(USO_API, bl.acronym)
            r = requests.get(url)
            if r.status_code == 200:
                dates = [datetime.strptime(s['date'], '%Y-%m-%d') for s in r.json()]
                articles = [d for d in dates if d.year == start.year and d.month == start.month]

            theses = []
            for thesis in ['msc_thesis', 'phd_thesis']:
                url = "{}publications/{}/{}/".format(USO_API, thesis, bl.acronym)
                r = requests.get(url)
                if r.status_code == 200:
                    dates = [datetime.strptime(s['date'], '%Y-%m-%d') for s in r.json()]
                    theses += [d for d in dates if d.year == start.year and d.month == start.month]

            KPIEntry.objects.update_or_create(beamline=bl, month=start.date(), kpi=KPI.objects.get(pk=PEER_REVIEWED_ARTICLES),
                                              defaults={'value':len(articles)})
            KPIEntry.objects.update_or_create(beamline=bl, month=start.date(), kpi=KPI.objects.get(pk=THESES),
                                              defaults={'value':len(theses)})


