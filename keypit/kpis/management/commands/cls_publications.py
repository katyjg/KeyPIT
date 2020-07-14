from django.conf import settings
from django.core.management.base import BaseCommand

from datetime import datetime
import re
import requests

from keypit.kpis.models import KPI, KPIEntry

USO_API = getattr(settings, 'USO_API', 'https://user.lightsource.ca/api/v1/')
PUBLICATION_KPIS = getattr(settings, 'PUBLICATION_KPIS', {
    5: ['article'],
    14: ['msc_thesis', 'phd_thesis'],
    15: ['pdb']
})


class Command(BaseCommand):
    help = """Fetches Publications from the CLS USO"""

    def handle(self, *args, **options):

        for pk, keys in PUBLICATION_KPIS.items():
            kpi = KPI.objects.get(pk=pk)
            for beamline in kpi.beamlines():
                publications = {}
                for bl in beamline.beamline_acronyms():
                    # Import Facility Publications
                    for kind in keys:
                        url = "{api}publications/{kind}/{bl}/".format(api=USO_API, kind=kind, bl=bl)
                        r = requests.get(url)
                        if r.status_code == 200:
                            dates = [(datetime(*[int(i) for i in re.split('\-+', s['date'])][:-1], 1), s['cite'])
                                     for s in r.json()]
                            for d, c in dates:
                                publications.setdefault(d, []).append(c)

                this_month = datetime.now().replace(day=1)
                first_month = publications and max(
                    min(publications.keys()), datetime(datetime.now().year - 5, 1, 1)) or this_month

                for dt, citations in publications.items():
                    citations = set(citations)
                    if dt >= first_month:
                        comments = '<ul>{}</ul>'.format(''.join(['<li>{}</li>'.format(c) for c in citations]))
                        KPIEntry.objects.update_or_create(beamline=beamline, month=dt, kpi=kpi,
                                                          defaults={'value': len(citations), 'comments': comments})

                while first_month <= this_month:
                    if first_month not in publications:
                        KPIEntry.objects.update_or_create(beamline=beamline, month=first_month, kpi=kpi,
                                                          defaults={'value': 0, 'comments': ''})
                    first_month = datetime(first_month.month == 12 and first_month.year + 1 or first_month.year,
                                           first_month.month == 12 and 1 or first_month.month + 1, 1)

