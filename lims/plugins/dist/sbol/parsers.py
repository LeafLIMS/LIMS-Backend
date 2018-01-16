import os
from io import StringIO, BytesIO
import csv
import uuid
from collections import OrderedDict

from django.db.models import Q

from Bio import SeqIO
from snekbol import snekbol

from lims.inventory.models import Item


class DesignFileParser:

    GENBANK_FEATURE_TYPES = (
        'primer_bind',
        'cds',
        'rbs',
        '5\'_utr',
        'promoter',
        '3\'_utr',
        'terminator',
        'unknown',
        'structual',  # Support EGF imports
    )

    SO_URI = 'http://identifiers.org/so/SO:'
    SO_MISC = SO_URI + '0000001'
    SO_PROMOTER = SO_URI + '0000167'
    SO_CDS = SO_URI + '0000316'
    SO_RBS = SO_URI + '0000139'
    SO_TERMINATOR = SO_URI + '0000141'
    SO_OPERATOR = SO_URI + '0000057'
    SO_INSULATOR = SO_URI + '0000627'
    SO_RIBONUCLEASE_SITE = SO_URI + '0001977'
    SO_RNA_STABILITY_ELEMENT = SO_URI + '0001979'
    SO_PROTEASE_SITE = SO_URI + '0001956'
    SO_PROTEIN_STABILITY_ELEMENT = SO_URI + '0001955'
    SO_ORIGIN_OF_REPLICATION = SO_URI + '0000296'
    SO_RESTRICTION_ENZYME_CUT_SITE = SO_URI + '0000168'

    SO_PRIMER_BINDING_SITE = SO_URI + '0005850'

    ROLES = {
        'promoter': SO_PROMOTER,
        'cds': SO_CDS,
        'ribosome entry site': SO_RBS,
        'rbs': SO_RBS,
        'terminator': SO_TERMINATOR,
        'operator': SO_OPERATOR,
        'insulator': SO_INSULATOR,
        'ribonuclease site': SO_RIBONUCLEASE_SITE,
        'rna stability element': SO_RNA_STABILITY_ELEMENT,
        'protease site': SO_PROTEASE_SITE,
        'protein stability element': SO_PROTEIN_STABILITY_ELEMENT,
        'origin of replication': SO_ORIGIN_OF_REPLICATION,
        'restriction site': SO_RESTRICTION_ENZYME_CUT_SITE,
        'primer binding site': SO_PRIMER_BINDING_SITE,
        'user defined': SO_MISC,
    }
    INVERT_ROLES = {v: k for k, v in ROLES.items()}

    def __init__(self, data):
        self.file_data = StringIO(initial_value=data)

        # This may need to be set as a setting
        self.default_uri = 'http://leaflims.github.io/'

        # SBOL specific stuff
        self.document = snekbol.Document(self.default_uri)
        self.construct = snekbol.ComponentDefinition('Construct')
        self.document.add_component_definition(self.construct)

    def name_to_identity(self, name):
        return name.replace(' ', '_')

    def get_inventory_item(self, name):
        """
        Get an item matching the name/identifier from the inventory
        """
        try:
            item = Item.objects.get(Q(name=name) | Q(identifier=name))
            return item
        except Item.DoesNotExist:
            return False

    def csv_to_sbol_component(self, element):
        """
        Take a CSV element and convert to an SBOL component
        """
        component_seq = snekbol.Sequence(self.name_to_identity(element['Name']),
                                         element['Sequence'])
        component = snekbol.ComponentDefinition(self.name_to_identity(element['Name']),
                                                roles=[self.ROLES.get(element['Role'],
                                                                      self.SO_MISC)],
                                                sequences=[component_seq])
        self.document.add_component_definition(component)
        return component

    def genbank_to_sbol_component(self, element, sequence, feature_type):
        """
        Create an SBOL component from a genbank element
        """
        component_seq = snekbol.Sequence(self.name_to_identity(element),
                                         sequence)
        component = snekbol.ComponentDefinition(self.name_to_identity(element),
                                                roles=[self.ROLES.get(feature_type,
                                                                      self.SO_MISC)],
                                                sequences=[component_seq])
        self.document.add_component_definition(component)
        return component

    def make_sbol_construct(self, elements):
        """
        Take all elements and sequences and make an SBOL construct from them
        """
        self.document.assemble_component(self.construct, elements)

    def make_sbol_xml(self):
        """
        Take an SBOL definition and turn into RDF/XML
        """
        xml_file = BytesIO()
        self.document.write(xml_file)
        xml_file.seek(0)
        return xml_file.read()

    def get_sbol_from_xml(self, source_data):
        """
        Read in SBOL XML from source data and set document
        """
        filename = '/tmp/' + str(uuid.uuid4()) + '.xml'
        with open(filename, 'w+') as sf:
            sf.write(self.file_data.read())
        self.document.read(filename)
        os.remove(filename)

    def sbol_to_list(self):
        """
        Take an sbol file and return a linear list of components
        """
        # Read in SBOL file
        # Look for component def with components
        # Build a list of SBOL componetns from this
        # If multiple do something fancy?
        elements = []
        self.document.read(self.file_data)
        for c in self.document.list_components():
            if len(c.components) > 0:
                comp_elems = []
                for cl in self.document.get_components(c.identity):
                    role_uri = cl.definition.roles[0]
                    comp_elems.append({'name': cl.display_id,
                                       'role': self.INVERT_ROLES[role_uri].replace(' ', '-')})
                elements.append(comp_elems)
        return elements

    def parse_sbol(self):
        """
        Take an SBOL XML file and parse to items/sbol
        """
        elements = self.sbol_to_list()
        items = []
        for e in elements:
            for c in e:
                item = self.get_inventory_item(c['name'])
                if item:
                    items.append(item)
        return items, elements

    def parse_gb(self):
        """
        Take a genbank file and parse to items/SBOL
        """
        items = []
        elements = OrderedDict()
        sbol = None
        try:
            record = SeqIO.read(self.file_data, 'genbank')
            features = record.features  # sorted(record.features, key=attrgetter('location.start'))
            for feat in features:
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
                        feature_type = feat.type.lower()
                        if feature_type == 'rbs':
                            feature_type = 'ribosome entry site'
                        elif feature_type == 'primer_bind':
                            feature_type = 'primer binding site'
                        seq = str(feat.extract(record.seq))
                        elements[name] = self.genbank_to_sbol_component(name, seq, feature_type)
                        item = self.get_inventory_item(name)
                        if item:
                            items.append(item)
        except Exception as e:
            print(e)
            pass
        else:
            if len(elements.values()) > 0:
                self.make_sbol_construct(list(elements.values()))
                sbol = self.make_sbol_xml()
        return items, sbol

    def parse_csv(self):
        reader = csv.DictReader(self.file_data)
        items = []
        elements = {}
        for line in reader:
            # Using the EGF style CSV file with the following
            # headers:
            # Name, Description, Role, Color, Sequence, @metadata

            # Create SBOL construct from the file
            if 'Name' in line and 'Role' in line:
                if line['Name'] not in elements:
                    elements[line['Name']] = self.csv_to_sbol_component(line)

            if 'Name' in line and line['Name'] != '':
                item = self.get_inventory_item(line['Name'])
                if item:
                    items.append(item)

        self.make_sbol_construct(list(elements.values()))
        sbol = self.make_sbol_xml()
        return items, sbol
