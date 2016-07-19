from Bio import SeqIO

from lims.projects.models import Design, Element, ElementLabel
from lims.inventory.models import ItemType
from lims.inventory.helpers import item_from_type


def genbank_to_design_elements(design: Design, text_file: str, request):
    record = SeqIO.read(text_file, 'genbank')
    links = []
    link_elements = {}
    for feat in record.features:
        if feat.type in ['primer_bind', 'CDS', "5'_UTR", 'Promoter', "3'_UTR", 'Terminator']:
            elem = Element(design=design)
            label = ''
            identifier = ''
            link_to = ''
            name = ''
            sequence = feat.extract(record.seq)
            for key, value in feat.qualifiers.items():
                if key == 'label':
                    name = value[0]
                if key == 'LIMS_LABEL':
                    label = value[0]
                if key == 'LIMS_CATALOGID':
                    identifier = value[0]
                if key == 'LIMS_LINKEDTO':
                    link_to = value[0]

            elem.name = name
            try:
                elem.label = ElementLabel.objects.get(name=label)
            except:
                elem.label, created = ElementLabel.objects.get_or_create(
                    name='Consumable',
                    type_of=ItemType.objects.get(name='Consumable'))

            if label and identifier:
                elem.inventory_item = item_from_type(elem.label.type_of,
                                                     identifier, name, request, str(sequence))

            if label:
                elem.save()

            if link_to:
                links.append([link_to, elem])
            else:
                link_elements[identifier] = elem

    for item in links:
        try:
            item[1].linked_to = link_elements[item[0]]
            item[1].save()
        except:
            pass
