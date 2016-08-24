import io
from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import FileTemplate, FileTemplateField


class FileTemplateTestCase(LoggedInTestCase):

    def setUp(self):
        super(FileTemplateTestCase, self).setUp()

        self._input_template1 = \
            FileTemplate.objects.create(name="InputTemplate1",
                                        file_for="input")
        self._input_template1_idfield = \
            FileTemplateField.objects.create(name="ID1Field1",
                                             required=True,
                                             is_identifier=True,
                                             template=self._input_template1)
        self._input_template1_field1 = \
            FileTemplateField.objects.create(name="1Field1",
                                             required=False,
                                             is_identifier=False,
                                             template=self._input_template1)
        self._input_template1_field2 = \
            FileTemplateField.objects.create(name="1Field2",
                                             required=True,
                                             is_identifier=False,
                                             template=self._input_template1)
        self._input_template2 = \
            FileTemplate.objects.create(name="InputTemplate2",
                                        file_for="input")
        self._input_template2_idfield1 = \
            FileTemplateField.objects.create(name="ID2Field1",
                                             required=True,
                                             is_identifier=True,
                                             template=self._input_template2)
        self._input_template2_idfield2 = \
            FileTemplateField.objects.create(name="ID2Field2",
                                             required=True,
                                             is_identifier=True,
                                             template=self._input_template2)
        self._input_template2_field1 = \
            FileTemplateField.objects.create(name="2Field1",
                                             required=False,
                                             is_identifier=False,
                                             template=self._input_template2)
        self._input_template2_field2 = \
            FileTemplateField.objects.create(name="2Field2",
                                             required=True,
                                             is_identifier=False,
                                             template=self._input_template2)
        self._output_template = \
            FileTemplate.objects.create(name="OutputTemplate",
                                        file_for="output")
        self._output_template_idfield = \
            FileTemplateField.objects.create(name="ID3Field1",
                                             required=True,
                                             is_identifier=True,
                                             template=self._output_template)
        self._output_template_field = \
            FileTemplateField.objects.create(name="3Field1",
                                             required=False,
                                             is_identifier=False,
                                             template=self._output_template)
        self._output_template_field = \
            FileTemplateField.objects.create(name="3Field2",
                                             required=True,
                                             is_identifier=False,
                                             template=self._output_template)

    def test_presets(self):
        self.assertIs(FileTemplate.objects.filter(name="InputTemplate1").exists(), True)
        templ1 = FileTemplate.objects.get(name="InputTemplate1")
        self.assertEqual(templ1.name, "InputTemplate1")
        self.assertEqual(templ1.file_for, "input")
        templ1_fields = templ1.fields.all()
        self.assertEqual(len(templ1_fields), 3)
        templ1_field1 = templ1_fields[0]
        self.assertEqual(templ1_field1.name, "ID1Field1")
        self.assertIs(templ1_field1.required, True)
        self.assertIs(templ1_field1.is_identifier, True)
        templ1_field2 = templ1_fields[1]
        self.assertEqual(templ1_field2.name, "1Field1")
        self.assertIs(templ1_field2.required, False)
        self.assertIs(templ1_field2.is_identifier, False)
        templ1_field3 = templ1_fields[2]
        self.assertEqual(templ1_field3.name, "1Field2")
        self.assertIs(templ1_field3.required, True)
        self.assertIs(templ1_field3.is_identifier, False)

        self.assertIs(FileTemplate.objects.filter(name="InputTemplate2").exists(), True)
        templ2 = FileTemplate.objects.get(name="InputTemplate2")
        self.assertEqual(templ2.name, "InputTemplate2")
        self.assertEqual(templ2.file_for, "input")
        templ2_fields = templ2.fields.all()
        self.assertEqual(len(templ2_fields), 4)
        templ2_field1 = templ2_fields[0]
        self.assertEqual(templ2_field1.name, "ID2Field1")
        self.assertIs(templ2_field1.required, True)
        self.assertIs(templ2_field1.is_identifier, True)
        templ2_field2 = templ2_fields[1]
        self.assertEqual(templ2_field2.name, "ID2Field2")
        self.assertIs(templ2_field2.required, True)
        self.assertIs(templ2_field2.is_identifier, True)
        templ2_field3 = templ2_fields[2]
        self.assertEqual(templ2_field3.name, "2Field1")
        self.assertIs(templ2_field3.required, False)
        self.assertIs(templ2_field3.is_identifier, False)
        templ2_field4 = templ2_fields[3]
        self.assertEqual(templ2_field4.name, "2Field2")
        self.assertIs(templ2_field4.required, True)
        self.assertIs(templ2_field4.is_identifier, False)

        self.assertIs(FileTemplate.objects.filter(name="OutputTemplate").exists(), True)
        templ3 = FileTemplate.objects.get(name="OutputTemplate")
        self.assertEqual(templ3.name, "OutputTemplate")
        self.assertEqual(templ3.file_for, "output")
        templ3_fields = templ3.fields.all()
        self.assertEqual(len(templ3_fields), 3)
        templ3_field1 = templ3_fields[0]
        self.assertEqual(templ3_field1.name, "ID3Field1")
        self.assertIs(templ3_field1.required, True)
        self.assertIs(templ3_field1.is_identifier, True)
        templ3_field2 = templ3_fields[1]
        self.assertEqual(templ3_field2.name, "3Field1")
        self.assertIs(templ3_field2.required, False)
        self.assertIs(templ3_field2.is_identifier, False)
        templ3_field3 = templ3_fields[2]
        self.assertEqual(templ3_field3.name, "3Field2")
        self.assertIs(templ3_field3.required, True)
        self.assertIs(templ3_field3.is_identifier, False)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/filetemplates/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/filetemplates/%d/' % self._input_template1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/filetemplates/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/filetemplates/%d/' % self._input_template1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/filetemplates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        templates = response.data
        self.assertEqual(len(templates["results"]), 3)
        templ1 = templates["results"][0]
        self.assertEqual(templ1["name"], "InputTemplate1")
        self.assertEqual(templ1["file_for"], "input")
        templ1_fields = templ1["fields"]
        self.assertEqual(len(templ1_fields), 3)
        templ1_field1 = templ1_fields[0]
        self.assertEqual(templ1_field1["name"], "ID1Field1")
        self.assertIs(templ1_field1["required"], True)
        self.assertIs(templ1_field1["is_identifier"], True)
        templ1_field2 = templ1_fields[1]
        self.assertEqual(templ1_field2["name"], "1Field1")
        self.assertIs(templ1_field2["required"], False)
        self.assertIs(templ1_field2["is_identifier"], False)
        templ1_field3 = templ1_fields[2]
        self.assertEqual(templ1_field3["name"], "1Field2")
        self.assertIs(templ1_field3["required"], True)
        self.assertIs(templ1_field3["is_identifier"], False)

    def test_user_view(self):
        self._asJoeBloggs()
        response = self._client.get('/filetemplates/%d/' % self._input_template1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        templ1 = response.data
        self.assertEqual(templ1["name"], "InputTemplate1")
        self.assertEqual(templ1["file_for"], "input")
        templ1_fields = templ1["fields"]
        self.assertEqual(len(templ1_fields), 3)
        templ1_field1 = templ1_fields[0]
        self.assertEqual(templ1_field1["name"], "ID1Field1")
        self.assertIs(templ1_field1["required"], True)
        self.assertIs(templ1_field1["is_identifier"], True)
        templ1_field2 = templ1_fields[1]
        self.assertEqual(templ1_field2["name"], "1Field1")
        self.assertIs(templ1_field2["required"], False)
        self.assertIs(templ1_field2["is_identifier"], False)
        templ1_field3 = templ1_fields[2]
        self.assertEqual(templ1_field3["name"], "1Field2")
        self.assertIs(templ1_field3["required"], True)
        self.assertIs(templ1_field3["is_identifier"], False)

    def test_user_create(self):
        self._asJaneDoe()
        new_template = {"name": "Test Template",
                        "file_for": "input",
                        "fields": [
                            {"name": "IDTestField",
                             "required": True,
                             "is_identifier": True
                             },
                            {"name": "TestField1",
                             "required": False,
                             "is_identifier": False
                             },
                            {"name": "TestField2",
                             "required": True,
                             "is_identifier": False
                             }
                        ]
                        }
        response = self._client.post("/filetemplates/", new_template, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_create(self):
        self._asAdmin()
        new_template = {"name": "Test Template",
                        "file_for": "input",
                        "fields": [
                            {"name": "IDTestField",
                             "required": True,
                             "is_identifier": True
                             },
                            {"name": "TestField1",
                             "required": False,
                             "is_identifier": False
                             },
                            {"name": "TestField2",
                             "required": True,
                             "is_identifier": False
                             }
                        ]
                        }
        response = self._client.post("/filetemplates/", new_template, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(FileTemplate.objects.count(), 4)
        self.assertIs(FileTemplate.objects.filter(name="Test Template").exists(), True)
        templ1 = FileTemplate.objects.get(name="Test Template")
        self.assertEqual(templ1.name, "Test Template")
        self.assertEqual(templ1.file_for, "input")
        templ1_fields = templ1.fields.all()
        self.assertEqual(len(templ1_fields), 3)
        templ1_field1 = templ1_fields[0]
        self.assertEqual(templ1_field1.name, "IDTestField")
        self.assertIs(templ1_field1.required, True)
        self.assertIs(templ1_field1.is_identifier, True)
        templ1_field2 = templ1_fields[1]
        self.assertEqual(templ1_field2.name, "TestField1")
        self.assertIs(templ1_field2.required, False)
        self.assertIs(templ1_field2.is_identifier, False)
        templ1_field3 = templ1_fields[2]
        self.assertEqual(templ1_field3.name, "TestField2")
        self.assertIs(templ1_field3.required, True)
        self.assertIs(templ1_field3.is_identifier, False)

    def test_user_edit(self):
        self._asJaneDoe()
        updated_template = {"name": "Test Template",
                            "file_for": "input",
                            "fields": [
                                {"name": "IDTestField",
                                 "required": True,
                                 "is_identifier": True
                                 },
                                {"name": "TestField1",
                                 "required": False,
                                 "is_identifier": False
                                 },
                                {"name": "TestField2",
                                 "required": True,
                                 "is_identifier": False
                                 }
                            ]
                            }
        response = self._client.patch("/filetemplates/%d/" % self._input_template1.id,
                                      updated_template, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_edit(self):
        self._asAdmin()
        updated_template = {"name": "Test Template",
                            "file_for": "input",
                            "fields": [
                                {"name": "IDTestField",
                                 "required": True,
                                 "is_identifier": True
                                 },
                                {"name": "TestField1",
                                 "required": False,
                                 "is_identifier": False
                                 },
                                {"name": "TestField2",
                                 "required": True,
                                 "is_identifier": False
                                 }
                            ]
                            }
        response = self._client.patch("/filetemplates/%d/" % self._input_template1.id,
                                      updated_template, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(FileTemplate.objects.filter(name="Test Template").exists(), True)
        templ1 = FileTemplate.objects.get(name="Test Template")
        self.assertEqual(templ1.name, "Test Template")
        self.assertEqual(templ1.file_for, "input")
        templ1_fields = templ1.fields.all()
        self.assertEqual(len(templ1_fields), 3)
        templ1_field1 = templ1_fields[0]
        self.assertEqual(templ1_field1.name, "IDTestField")
        self.assertIs(templ1_field1.required, True)
        self.assertIs(templ1_field1.is_identifier, True)
        templ1_field2 = templ1_fields[1]
        self.assertEqual(templ1_field2.name, "TestField1")
        self.assertIs(templ1_field2.required, False)
        self.assertIs(templ1_field2.is_identifier, False)
        templ1_field3 = templ1_fields[2]
        self.assertEqual(templ1_field3.name, "TestField2")
        self.assertIs(templ1_field3.required, True)
        self.assertIs(templ1_field3.is_identifier, False)

    def test_user_delete(self):
        self._asJoeBloggs()
        response = self._client.delete("/filetemplates/%d/" % self._input_template1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete("/filetemplates/%d/" % self._input_template1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIs(FileTemplate.objects.filter(name="InputTemplate1").exists(), False)

    def test_read_file(self):
        # Read a 3-line file with all the correct fields ID1Field1 (req+ident), 1Field1, 1Field2 (req)
        file = io.StringIO("ID1Field1,1Field1,1Field2\nA,B,C\nD,E,F")
        result = self._input_template1.read(file)
        file.close()
        self.assertIsNot(result, False)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[frozenset("A")], {"1Field1": "B", "1Field2": "C"})
        self.assertEqual(result[frozenset("D")], {"1Field1": "E", "1Field2": "F"})
        # Read a file with extra fields (expect them to be preserved)
        file = io.StringIO("ID1Field1,1Field1,1Field2,ExtraField\nA,B,C,X\nD,E,F,Y")
        result = self._input_template1.read(file)
        file.close()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[frozenset("A")], {"1Field1": "B", "1Field2": "C", "ExtraField": "X"})
        self.assertEqual(result[frozenset("D")], {"1Field1": "E", "1Field2": "F", "ExtraField": "Y"})
        # Read a file with non-required fields missing
        file = io.StringIO("ID1Field1,1Field2\nA,C\nD,F")
        result = self._input_template1.read(file)
        file.close()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[frozenset("A")], {"1Field2": "C"})
        self.assertEqual(result[frozenset("D")], {"1Field2": "F"})
        # Read a file with required fields missing
        file = io.StringIO("ID1Field1,1Field1\nA,B\nD,E")
        result = self._input_template1.read(file)
        file.close()
        self.assertIs(result, False)
        # Read a non-CSV file
        file = io.StringIO("What a lot of rubbish\nThis file should never work\nBut it might!")
        try:
            result = self._input_template1.read(file)
        except:
            result = False
        file.close()
        self.assertIs(result, False)

    def test_write_file(self):
        data1 = [{"ID1Field1": "a", "1Field1": "b", "1Field2": "c"}, {"ID1Field1": "d", "1Field1": "e", "1Field2": "f"}]
        data2 = [{"ID1Field1": "a", "1Field1": "b", "1Field2": "c", "Extra1": "x"},
                 {"ID1Field1": "d", "1Field1": "e", "1Field2": "f", "Extra2": "y"}]
        data3 = [{"ID1Field1": "a", "1Field2": "c"}, {"ID1Field1": "d", "1Field1": "e"}]
        expectedContentA = "ID1Field1,1Field1,1Field2\na,b,c\nd,e,f\n"
        expectedContentB = "ID1Field1,1Field1,1Field2\na,,c\nd,e,\n"
        # Write a file and check contents are correct
        file = io.StringIO()
        self._input_template1.write(file, data1)
        self.assertEqual(file.getvalue(), expectedContentA)
        file.close()
        # Write a file with extra columns and check output does not include them
        file = io.StringIO()
        self._input_template1.write(file, data2)
        self.assertEqual(file.getvalue(), expectedContentA)
        file.close()
        # Write a file with missing columns and check output includes headers anyway
        file = io.StringIO()
        self._input_template1.write(file, data3)
        self.assertEqual(file.getvalue(), expectedContentB)
        file.close()
