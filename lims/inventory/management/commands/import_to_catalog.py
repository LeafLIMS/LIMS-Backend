import csv

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from lims.inventory.models import Catalog, Tag, Part, Primer, RestrictionEnzyme

class Command(BaseCommand):
    help = 'Imports a CSV of items into a inventory'

    def add_arguments(self, parser):
        parser.add_argument('inventory_id', type=int)
        parser.add_argument('username')
        parser.add_argument('csv_file')

    def emptyToNumber(self, line, item):
        for field in line:
            ft = item._meta.get_field(field).get_internal_type()
            if ft in ['FloatField', 'IntegerField'] and getattr(item, field) == '':
                setattr(item, field, '0')

    def handle(self, *args, **options):
        user = User.objects.get(username=options['username'])
        inventory = Catalog.objects.get(pk=options['inventory_id'])

        for line in csv.DictReader(open(options['csv_file'])):

            tags = []
            if 'tags' in line:
                tags = line['tags'].split(', ')
                del line['tags']

            if inventory.content_type.model == 'primer':
                item = Primer(added_by=user, **line)
            elif inventory.content_type.model == 'part':
                item = Part(added_by=user, **line)
            elif inventory.content_type.model == 'restrictionenzyme':
                item = RestrictionEnzyme(added_by=user, **line)

            self.emptyToNumber(line, item)
            item.save()

            if len(tags) > 0:
                for tag_name in tags:
                    if tag_name != '':
                        t, created = Tag.objects.get_or_create(name=tag_name)
                        item.tags.add(t)

            inventory.related.connect(item)
