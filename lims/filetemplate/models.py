import csv

from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class FileTemplate(models.Model):
    FILE_FOR_CHOICES = (
        ('input', 'Input'),
        ('output', 'Output'),
    )

    name = models.CharField(max_length=200, db_index=True, unique=True)
    file_for = models.CharField(max_length=6, choices=FILE_FOR_CHOICES)

    def field_name(self):
        return self.name.lower().replace(' ', '_')

    def read(self, input_file):
        csv_file = csv.DictReader(input_file)
        try:
            identifier_fields = self.fields.filter(is_identifier=True)
        except ObjectDoesNotExist:
            return False
        else:
            indexed = {}
            if self._validate_headers(csv_file.fieldnames):
                # TODO: Discard extra fields not in headers?
                for line in csv_file:
                    line = dict([(k, v) for k, v in line.items() if v.strip()])
                    if any(line):
                        identifier = frozenset(line[n.name] for n in identifier_fields)
                        # Get a list of identifiers and remove from line
                        ifn = [i.name for i in identifier_fields]
                        line = dict([(k, v) for k, v in line.items() if k not in ifn])
                        indexed[identifier] = line
                return indexed
        return False

    def _validate_headers(self, header_list):
        for field in self.fields.all():
            if field.required and field.name not in header_list:
                return False
        return True

    def write(self, output_file, data):
        fieldnames = [item.name for item in self.fields.all()]
        csv_output = csv.DictWriter(output_file, fieldnames=fieldnames,
                                    extrasaction='ignore', lineterminator='\n')
        csv_output.writeheader()
        csv_output.writerows(data)
        return output_file

    def __str__(self):
        return self.name


class FileTemplateField(models.Model):
    name = models.CharField(max_length=50)
    required = models.BooleanField(default=False)
    is_identifier = models.BooleanField(default=False)

    template = models.ForeignKey(FileTemplate, related_name='fields')

    def __str__(self):
        return self.name
