import os

from django.conf import settings
from django.core.files import File

from lims.inventory.models import Item

from lims.projects.providers import ProductPluginProvider
from .parsers import DesignFileParser


class SBOLParser(ProductPluginProvider):
    properties_src = 'll_sbol'

    def _parse_design(self, instance):
        """
        Takes a design file and extracts the necessary info
        out to add inventory items or other things.

        Looks for "design_file" property containing the contents of a design file. If found
        will save this to a file and generate an SBOL version (if not already SBOL) along
        with an SBOL diagram. File paths will be saved as "design_file_path" and
        "sbol_file_path" with the diagram being stores as part of the property.
        """
        # Check that the plugin data is available
        if instance.properties and self.properties_src in instance.properties:
            sbol_properties = instance.properties[self.properties_src]
            # Look for a design and parse to SBOL file + SBOL diagram code
            # Save the design to a file and remove from properties
            if 'design_file' in sbol_properties and sbol_properties['design_file']:
                # First write out the design file
                sbol_properties['design_file_path'] = \
                    self.write_design_file(sbol_properties['design_file'],
                                           sbol_properties['design_file_extension'],
                                           instance)

                items = []
                sbol = ""
                parser = DesignFileParser(sbol_properties['design_file'])
                if sbol_properties['design_file_extension'] == 'csv':
                    items, sbol = parser.parse_csv()
                elif sbol_properties['design_file_extension'] == 'gb':
                    items, sbol = parser.parse_gb()

                sbol_properties['sbol_file_path'] = self.write_sbol_file(sbol, instance)

                for i in items:
                    instance.linked_inventory.add(i)

                # Remove the design file data as not to clog up requests with potentially
                # large files.
                del sbol_properties['design_file']

                instance.save()

    def write_sbol_file(self, sbol_data, instance):
        os.makedirs("{root}designs/".format(root=settings.MEDIA_ROOT), exist_ok=True)
        file_name = '{name}.sbol'.format(name=instance.product_identifier)
        file_path = "{root}designs/{name}.sbol".format(root=settings.MEDIA_ROOT,
                                                       name=file_name)
        with open(file_path, 'w+') as f:
            design_file = File(f)
            design_file.write(sbol_data.decode())
        return file_name

    def write_design_file(self, file_data, extension, instance):
        os.makedirs("{root}designs/".format(root=settings.MEDIA_ROOT), exist_ok=True)
        file_name = '{name}.{ext}'.format(name=instance.product_identifier,
                                          ext=extension)
        file_path = "{root}designs/{filename}".format(root=settings.MEDIA_ROOT,
                                                      filename=file_name)
        try:
            with open(file_path, 'w+') as f:
                design_file = File(f)
                design_file.write(file_data)
        except:
            file_name = ""
        return file_name

    def read_sbol_file(self, instance):
        file_name = '{name}.sbol'.format(name=instance.product_identifier)
        file_path = "{root}designs/{name}".format(root=settings.MEDIA_ROOT,
                                                  name=file_name)
        try:
            with open(file_path, 'r') as f:
                design_file = File(f)
                file_contents = design_file.read()
        except:
            file_contents = False
        return file_contents

    def get_sbol_design(self, instance):
        if instance.properties and self.properties_src in instance.properties:
            sbol_properties = instance.properties[self.properties_src]
            if 'sbol_file_path' in sbol_properties and sbol_properties['sbol_file_path']:
                sbol_data = self.read_sbol_file(instance)
                if sbol_data:
                    parser = DesignFileParser(sbol_data)
                    elements = parser.sbol_to_list()
                    for e in elements:
                        for sub in e:
                            try:
                                item = Item.objects.get(name=sub['name'])
                            except Item.DoesNotExist:
                                pass
                            else:
                                sub['item'] = item.id
                    sbol_properties['sbol_diagram'] = elements

    def create(self):
        self._parse_design(self.item)
        self.get_sbol_design(self.item)

    def update(self):
        self._parse_design(self.item)
        self.get_sbol_design(self.item)

    def view(self):
        self.get_sbol_design(self.item)
