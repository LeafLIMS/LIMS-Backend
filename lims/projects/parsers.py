from io import StringIO
import csv

from django.db.models import Q

from Bio import SeqIO

from lims.inventory.models import Item


class DesignFileParser:

    GENBANK_FEATURE_TYPES = (
        'primer_bind',
        'cds',
        '5\'_utr',
        'promoter',
        '3\'_utr',
        'terminator',
        'unknown',
        'structual',  # Support EGF imports
    )

    def __init__(self, data):
        self.file_data = StringIO(initial_value=data)

    def get_inventory_item(self, name):
        """
        Get an item matching the name/identifier from the inventory
        """
        try:
            item = Item.objects.get(Q(name=name) | Q(identifier=name))
            return item
        except Item.DoesNotExist:
            return False

    def parse_gb(self):
        items = []
        try:
            record = SeqIO.read(self.file_data, 'genbank')
            for feat in record.features:
                # The file sometimes has lowercase and sometimes uppercase
                # types so normalise to lowercase.
                if feat.type.lower() in self.GENBANK_FEATURE_TYPES:
                    name = ''
                    # Look for the label key. Other keys can be set but
                    # most software simply sets the label key and nothing
                    # else.
                    for key, value in feat.qualifiers.items():
                        if key == 'label':
                            name = value[0]
                    if name:
                        item = self.get_inventory_item(name)
                        if item:
                            items.append(item)
        except:
            pass
        return items

    def parse_csv(self):
        reader = csv.DictReader(self.file_data)
        items = []
        for line in reader:
            # Using the EGF style CSV file with the following
            # headers:
            # Name, Description, Role, Color, Sequence, @metadata
            # Ignoring all but the name fields for now as we don't
            # need the others.
            if 'Name' in line and line['Name'] != '':
                item = self.get_inventory_item(line['Name'])
                if item:
                    items.append(item)
        return items
