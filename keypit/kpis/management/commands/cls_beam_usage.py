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

def format_localtime(dt):
    return datetime.strftime(timezone.localtime(dt), '%Y-%m-%dT%H')
    return datetime.strftime(timezone.localtime(pytz.utc.localize(dt)), '%Y-%m-%dT%H')


class Command(BaseCommand):
    help = """Fetches Publications and Scheduling KPIs information from the CLS USO
                - provide an optional --date in the format yyyy-mm-dd"""

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str)
        parser.add_argument('--month', type=int)
        parser.add_argument('--year', type=int)

    def handle(self, *args, **options):
        if options.get('date'):
            dt = datetime.strptime(options.get('date'), '%Y-%m-%d')
        elif options.get('year'):
            dt = datetime(options.get('year'), options.get('month', 1), 1)
        else:
            dt = datetime.now().replace(day=1) - timedelta(days=1)
        start = timezone.make_aware(dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
        end = timezone.make_aware(datetime(dt.month == 12 and dt.year + 1 or dt.year, dt.month == 12 and 1 or dt.month + 1, 1))
        qstart = datetime.strftime(start, '%Y-%m-%d')
        qend = datetime.strftime(end, '%Y-%m-%d')

        # Import Modes
        n_shifts = []
        url = "{}schedule/modes/?start={}&end={}".format(USO_API, qstart, qend)
        r = requests.get(url)
        if r.status_code == 200:
            modes = [s for s in r.json() if s['kind'] == 'N' and not s['cancelled']]
            for mode in modes:
                st = pytz.utc.localize(datetime.strptime(mode['start'], '%Y-%m-%dT%H:%M:%SZ'))
                ed = pytz.utc.localize(datetime.strptime(mode['end'], '%Y-%m-%dT%H:%M:%SZ'))
                while st < ed:
                    if st >= start and st < end: n_shifts.append(format_localtime(st))
                    st += timedelta(hours=8)
        n_shifts = set(n_shifts)

        for beamline in Beamline.objects.all():
            bl_n_shifts = 0
            bl_used_shifts = 0
            for bl in beamline.beamline_acronyms():
                # Import Facility Schedule(s)
                url = "{}schedule/beamtime/{}/?start={}&end={}".format(USO_API, bl, qstart, qend)
                r = requests.get(url)
                if r.status_code == 200:
                    visits = [s for s in r.json() if not s['cancelled']]
                    shifts = []
                    for visit in visits:
                        st = pytz.utc.localize(datetime.strptime(visit['start'], '%Y-%m-%dT%H:%M:%SZ'))
                        ed = pytz.utc.localize(datetime.strptime(visit['end'], '%Y-%m-%dT%H:%M:%SZ'))
                        while st < ed:
                            if st >= start and st < end: shifts.append(format_localtime(st))
                            st += timedelta(hours=8)
                else:
                    shifts = []
                    print("Schedule not found for {}".format(bl))
                bl_n_shifts += len(n_shifts)
                bl_used_shifts += len(n_shifts.intersection(set(shifts)))
                #percent_used = n_shifts and 100. * used_shifts / len(n_shifts) or 0

                #KPIEntry.objects.filter(beamline=bl, month=start.date(), kpi__id=BEAMLINE_AVAILABILITY, defaults={'value': percent_used})

            KPIEntry.objects.update_or_create(beamline=beamline, month=start, kpi=KPI.objects.get(pk=TOTAL_NORMAL_SHIFTS),
                                              defaults={'value': bl_n_shifts})
            KPIEntry.objects.update_or_create(beamline=beamline, month=start.date(), kpi=KPI.objects.get(pk=TOTAL_SHIFTS_USED),
                                              defaults={'value': bl_used_shifts})
