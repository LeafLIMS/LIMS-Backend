import os
from io import StringIO
import csv
import uuid
import xml.etree.ElementTree as ET

from django.db.models import Q

from Bio import SeqIO
import sbol

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

    # SBOL file namespaces
    SN = {
        'dcterms': 'http://purl.org/dc/terms/',
        'prov': 'http://www.w3.org/ns/prov#',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'sbol': 'http://sbols.org/v2#',
    }

    SO_OPERATOR = sbol.SO + '0000057'
    SO_INSULATOR = sbol.SO + '0000627'
    SO_RIBONUCLEASE_SITE = sbol.SO + '0001977'
    SO_RNA_STABILITY_ELEMENT = sbol.SO + '0001979'
    SO_PROTEASE_SITE = sbol.SO + '0001956'
    SO_PROTEIN_STABILITY_ELEMENT = sbol.SO + '0001955'
    SO_ORIGIN_OF_REPLICATION = sbol.SO + '0000296'
    SO_RESTRICTION_ENZYME_CUT_SITE = sbol.SO + '0000168'

    ROLES = {
        'promoter': sbol.SO_PROMOTER,
        'cds': sbol.SO_CDS,
        'ribosome entry site': sbol.SO_RBS,
        'terminator': sbol.SO_TERMINATOR,
        'operator': SO_OPERATOR,
        'insulator': SO_INSULATOR,
        'ribonuclease site': SO_RIBONUCLEASE_SITE,
        'rna stability element': SO_RNA_STABILITY_ELEMENT,
        'protease site': SO_PROTEASE_SITE,
        'protein stability element': SO_PROTEIN_STABILITY_ELEMENT,
        'origin of replication': SO_ORIGIN_OF_REPLICATION,
        'restriction site': SO_RESTRICTION_ENZYME_CUT_SITE,
        'user defined': sbol.SO_MISC,
    }

    INVERT_ROLES = {v: k for k, v in ROLES.items()}

    def __init__(self, data):
        self.file_data = StringIO(initial_value=data)

        # This may need to be set as a setting
        self.homespace_uri = 'http://leaflims.github.io'

        # SBOL specific stuff
        sbol.setHomespace(self.homespace_uri)
        self.document = sbol.Document()
        self.construct = sbol.ComponentDefinition('Construct')
        self.construct_seq = sbol.Sequence('Construct')
        self.document.addComponentDefinition(self.construct)

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
        # Sequences currently cause a segfault when added to document
        # component_seq = sbol.Sequence(element['Name'], element['Sequence'])
        # self.document.addSequence(component_seq)

        component = sbol.ComponentDefinition(element['Name'])
        component.roles.set(self.ROLES.get(element['Role'], sbol.SO_MISC))
        # component.sequences.set(component_seq.identity.get())
        self.document.addComponentDefinition(component)
        return component

    def genbank_to_sbol_component(self, element):
        """
        Create an SBOL component from a genbank element
        """
        component = sbol.ComponentDefinition(element)
        component.roles.set(sbol.SO_MISC)
        self.document.addComponentDefinition(component)
        return component

    def make_sbol_construct(self, elements):
        """
        Take all elements and sequences and make an SBOL construct from them
        """
        self.construct.assemble(elements)
        # Again, enable when doesn't cause segfault
        # self.construct_seq.assemble()

    def make_sbol_xml(self):
        """
        Take an SBOL definition and turn into RDF/XML
        """
        filename = '/tmp/' + str(uuid.uuid4()) + '.xml'
        self.document.write(filename)
        with open(filename) as sf:
            return sf.read()

    def get_sbol_from_xml(self, source_data):
        """
        Read in SBOL XML from source data and set document
        """
        filename = '/tmp/' + str(uuid.uuid4()) + '.xml'
        with open(filename, 'w+') as sf:
            sf.write(self.file_data.read())
        self.document.read(filename)
        os.remove(filename)

    def _ns_attr(self, namespace, attribute):
        return '{'+self.SN[namespace]+'}'+attribute

    def sbol_to_list(self):
        """
        Take an sbol file and return a linear list of components
        """
        construct_uri = self.homespace_uri + '/ComponentDefinition/Construct/1.0.0'
        """
        # Oh look, MORE segfaults! Wait until SWIG wrapper is wrapped!
        self.get_sbol_from_xml(self.file_data)
        construct = self.document.getComponentDefinition(construct_uri)
        print(construct)
        """
        elements = []
        construct_lookup = {}
        construct = None
        root = ET.fromstring(self.file_data.read())
        for cd in root:
            # Look for the "Construct" uri
            if cd.attrib[self._ns_attr('rdf', 'about')] == construct_uri:
                construct = cd
            else:
                uri = cd.attrib[self._ns_attr('rdf', 'about')]
                name = cd.find('sbol:displayId', self.SN).text
                role = cd.find('sbol:role', self.SN)
                role_uri = role.attrib[self._ns_attr('rdf', 'resource')]
                construct_lookup[uri] = {
                    'name': name,
                    'role': self.INVERT_ROLES[role_uri].replace(' ', '-')
                    }
        for c in construct.findall('sbol:component', self.SN):
            component = c.find('sbol:Component', self.SN)
            # Elements: {name:, role:}
            component_uri = component.find('sbol:definition', self.SN).attrib[
                    self._ns_attr('rdf', 'resource')]
            elements.append(construct_lookup[component_uri])
        return elements

    def parse_sbol(self):
        """
        Take an SBOL XML file and parse to items/sbol
        """
        self.get_sbol_from_xml(self.file_data)

    def parse_gb(self):
        """
        Take a genbank file and parse to items/SBOL
        """
        items = []
        elements = {}
        sbol = None
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
                        elements[name] = self.genbank_to_sbol_component(name)
                        item = self.get_inventory_item(name)
                        if item:
                            items.append(item)
        except:
            pass
        else:
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
