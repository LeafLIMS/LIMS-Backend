import csv

from django.db import models
import reversion
from django.core.exceptions import ObjectDoesNotExist


@reversion.register()
class FileTemplate(models.Model):
    FILE_FOR_CHOICES = (
        ('input', 'Input'),
        ('equip', 'Equipment'),
        ('output', 'Output'),
    )

    name = models.CharField(max_length=200, db_index=True, unique=True)
    file_for = models.CharField(max_length=6, choices=FILE_FOR_CHOICES)

    # Task specific options
    # Output each input item (excluding labware) by line rather than product
    use_inputs = models.BooleanField(default=False)
    # Collate inputs, only provide total amounts from task
    # By default each input is broken down per product
    total_inputs_only = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def field_name(self):
        return self.name.lower().replace(' ', '_')

    def _get_field_key(self, field):
        if field.map_to:
            return field.map_to
        return field.name

    def _validate_headers(self, header_list):
        if header_list is None:
            return False
        for field in self.fields.all():
            if field.required and field.name not in header_list:
                return False
        return True

    def read(self, input_file, as_list=False):
        csv_file = csv.DictReader(input_file)
        try:
            identifier_fields = self.fields.filter(is_identifier=True)
        except ObjectDoesNotExist:
            return False
        else:
            if as_list:
                indexed = []
            else:
                indexed = {}
            if self._validate_headers(csv_file.fieldnames):
                for line in csv_file:
                    line = dict([(k, v) for k, v in line.items() if v.strip()])
                    if any(line):
                        # Get the identifier fields from the file
                        identifier = frozenset(line[n.name] for n in identifier_fields)
                        # Get a list of identifiers and remove from line
                        ifn = [i.name for i in identifier_fields]
                        # We don't want to used identifiers if it's a list as they'll be
                        # discarded.
                        if as_list and len(ifn) > 0:
                            return False

                        generated_line = {}
                        # TODO: Currently we discard extra fields in CSV that are not in
                        # filetemplate. Change this?
                        for field in self.fields.all():
                            # Don't add identifier fields
                            if field.name not in ifn and field.name in line:
                                field_value = line[field.name]
                                # May map to different DB field
                                field_key = self._get_field_key(field)
                                if field.is_property:
                                    if 'properties' not in generated_line:
                                        generated_line['properties'] = []
                                    prop = {
                                        'name': field_key,
                                        'value': field_value
                                    }
                                    generated_line['properties'].append(prop)
                                else:
                                    generated_line[field_key] = field_value

                        if as_list:
                            indexed.append(generated_line)
                        else:
                            indexed[identifier] = generated_line
                return indexed
        return False

    def write(self, output_file, data, column_order='name'):
        fieldnames = [item.name for item in self.fields.all().order_by(column_order)]
        csv_output = csv.DictWriter(output_file, fieldnames=fieldnames,
                                    extrasaction='ignore', lineterminator='\n')
        csv_output.writeheader()
        csv_output.writerows(data)
        return output_file

    def __str__(self):
        return self.name


@reversion.register()
class FileTemplateField(models.Model):
    # Name of the field in the file
    name = models.CharField(max_length=50)
    # Name of the field in the DB (if different to file header)
    map_to = models.CharField(max_length=50, null=True, blank=True)
    required = models.BooleanField(default=False)
    is_identifier = models.BooleanField(default=False)
    # Is to be used as/read from a property not a field
    # Ignore on anything that does not support reading/writing
    # properties on objects.
    is_property = models.BooleanField(default=False)

    template = models.ForeignKey(FileTemplate, related_name='fields')

    def get_key(self):
        if self.map_to:
            return self.map_to
        return self.name

    def key_to_path(self):
        key = self.get_key()
        return key.split('.')

    def __str__(self):
        return self.name
