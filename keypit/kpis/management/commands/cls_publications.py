from django.conf import settings
from django.core.management.base import BaseCommand

from datetime import datetime, timedelta
import re
import requests

from keypit.kpis.models import Beamline, KPI, KPIEntry

USO_API = getattr(settings, 'USO_API', 'https://user.lightsource.ca/api/v1/')

PEER_REVIEWED_ARTICLES = 5
THESES = 14


class Command(BaseCommand):
    help = """Fetches Publications from the CLS USO"""

    def handle(self, *args, **options):

        for beamline in Beamline.objects.all():
            articles = {}
            theses = {}
            for bl in beamline.beamline_acronyms():
                # Import Facility Publications
                url = "{}publications/article/{}/".format(USO_API, bl)
                r = requests.get(url)
                if r.status_code == 200:
                    dates = [(datetime(*[int(i) for i in re.split('\-+', s['date'])][:-1], 1), s['cite'])
                             for s in r.json()]
                    for d, c in dates:
                        articles.setdefault(d, []).append(c)

                for thesis in ['msc_thesis', 'phd_thesis']:
                    url = "{}publications/{}/{}/".format(USO_API, thesis, bl)
                    r = requests.get(url)
                    if r.status_code == 200:
                        dates = [(datetime(*[int(i) for i in re.split('\-+', s['date'])][:-1], 1), s['cite'])
                                 for s in r.json()]
                        for d, c in dates:
                            theses.setdefault(d, []).append(c)

            for dt, citations in articles.items():
                if dt.year >= datetime.now().year - 5:
                    comments = '<ul>{}</ul>'.format(''.join(['<li>{}</li>'.format(c) for c in citations]))
                    KPIEntry.objects.update_or_create(beamline=beamline, month=dt, kpi=KPI.objects.get(pk=PEER_REVIEWED_ARTICLES),
                                                      defaults={'value': len(citations), 'comments': comments})
            for dt, citations in theses.items():
                if dt.year >= datetime.now().year - 5:
                    comments = '<ul>{}</ul>'.format(''.join(['<li>{}</li>'.format(c) for c in citations]))
                    KPIEntry.objects.update_or_create(beamline=beamline, month=dt, kpi=KPI.objects.get(pk=THESES),
                                                  defaults={'value': len(citations), 'comments': comments})
