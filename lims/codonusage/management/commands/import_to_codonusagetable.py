import re

from django.core.management.base import BaseCommand

from lims.codonusage.models import CodonUsageTable, CodonUsage


class Command(BaseCommand):
    help = 'Imports a codon usgae file into the database'

    def add_arguments(self, parser):
        parser.add_argument('table_id', type=int)
        parser.add_argument('table_file')

    def handle(self, *args, **options):
        table = CodonUsageTable.objects.get(pk=options['table_id'])
        with open(options['table_file']) as table_file:
            for line in table_file:
                groups = re.findall(r'\w{3} +(\w{3}) +[0-9\.]+ +([0-9\.]+) +[0-9\.]+', line)
                if len(groups) > 0:
                    values = groups[0]
                    c = CodonUsage(name=values[0], value=values[1], table=table)
                    c.save()
