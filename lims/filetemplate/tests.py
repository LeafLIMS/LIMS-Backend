from io import StringIO

from django.test import TestCase

from .models import FileTemplate, FileTemplateField

class FileTemplateTestCase(TestCase):

    def setUp(self):
        wt = FileTemplate.objects.create(name='Write Template')
        FileTemplateField.objects.create(template=wt, name='Name', is_identifier=True)
        FileTemplateField.objects.create(template=wt, name='Colour')
        FileTemplateField.objects.create(template=wt, name='Random')

        rt = FileTemplate.objects.create(name='Read Template')
        FileTemplateField.objects.create(template=rt, name='Name', is_identifier=True)
        FileTemplateField.objects.create(template=rt, name='Colour')
        FileTemplateField.objects.create(template=rt, name='Random')

        self.read_handle = StringIO("Name,Colour,Random\nBob,Red,13\nDave,Blue,26")
        self.write_handle = StringIO("")

    def test_can_read_template(self): 
        ft = FileTemplate.objects.get(name='Read Template')
        expected = {
            'Bob': {'Name': 'Bob', 'Colour': 'Red', 'Random': '13'},
            'Dave': {'Name': 'Dave', 'Colour': 'Blue', 'Random': '26'},
        }
        self.assertEqual(ft.read(self.read_handle), expected)

    def test_can_write_template(self): 
        ft = FileTemplate.objects.get(name='Write Template')
        expected = "Name,Colour,Random\nBob,Red,13\nDave,Blue,26\n"
        data = [ 
            {'Name': 'Bob', 'Colour': 'Red', 'Random': '13'},
            {'Name': 'Dave', 'Colour': 'Blue', 'Random': '26'},
        ]
        outputed_file = ft.write(self.write_handle, data)
        outputed_file.seek(0)
        self.assertEqual(outputed_file.read(), expected)
