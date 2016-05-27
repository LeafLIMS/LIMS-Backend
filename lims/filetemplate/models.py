import csv

from django.db import models

class FileTemplate(models.Model):
    name = models.CharField(max_length=200, db_index=True)

    def read(self, input_file):
        csv_file = csv.DictReader(input_file) 
        try:
            identifier_field = self.fields.get(is_identifier=True)
        except ObjectDoesNotExist:
            return False
        else:
            indexed = {}
            if self._validate_headers(csv_file.fieldnames):
                for line in csv_file:
                    identifier = line[identifier_field.name]
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
        csv_output = csv.DictWriter(output_file, fieldnames=fieldnames, extrasaction='ignore', lineterminator='\n')
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
