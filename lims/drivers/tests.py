from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import CopyFileDriver, CopyFilePath
from lims.equipment.models import Equipment, Location
import os
import filecmp
import tempfile


class CopyFileDriverTestCase(LoggedInTestCase):
    def setUp(self):
        super(CopyFileDriverTestCase, self).setUp()
        self._location = Location.objects.create(name="Bench", code="B1")
        self._equipmentSequencer = Equipment.objects.create(name="Sequencer",
                                                            location=self._location,
                                                            status="active", can_reserve=True)
        self._copyFile = \
            CopyFileDriver.objects.create(name="Copy1",
                                          equipment=self._equipmentSequencer,
                                          copy_from_prefix=tempfile.gettempdir(),
                                          copy_to_prefix=tempfile.gettempdir(),
                                          is_enabled=True)
        self._copyFilePath = \
            CopyFilePath.objects.create(
                driver=self._copyFile,
                copy_from="{project_identifier}{product_identifier}{run_identifier}A",
                copy_to="{project_identifier}{product_identifier}{run_identifier}B")
        self._copyFile.locations.add(self._copyFilePath)

    def test_presets(self):
        self.assertEqual(CopyFileDriver.objects.count(), 1)
        self.assertIs(CopyFileDriver.objects.filter(name="Copy1").exists(), True)
        copy1 = CopyFileDriver.objects.get(name="Copy1")
        self.assertEqual(copy1.equipment, self._equipmentSequencer)
        self.assertEqual(copy1.copy_from_prefix, tempfile.gettempdir())
        self.assertEqual(copy1.copy_to_prefix, tempfile.gettempdir())
        self.assertIs(copy1.is_enabled, True)
        self.assertEqual(copy1.locations.count(), 1)
        cfp = copy1.locations.all()[0]
        self.assertEqual(cfp.copy_from,
                         "{project_identifier}{product_identifier}{run_identifier}A")
        self.assertEqual(cfp.copy_to,
                         "{project_identifier}{product_identifier}{run_identifier}B")

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/copyfiles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/copyfiles/%d/' % self._copyFile.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/copyfiles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/copyfiles/%d/' % self._copyFile.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # No permissions restrictions so any user/admin can do anything
        self._asJoeBloggs()
        response = self._client.get('/copyfiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        copyfiles = response.data
        self.assertEqual(len(copyfiles["results"]), 1)
        copy1 = copyfiles["results"][0]
        self.assertEqual(copy1["name"], "Copy1")

    def test_user_view(self):
        self._asJoeBloggs()
        response = self._client.get('/copyfiles/%d/' % self._copyFile.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        copy1 = response.data
        self.assertEqual(copy1["name"], "Copy1")

    def test_admin_list(self):
        # No permissions restrictions so any user/admin can do anything
        self._asAdmin()
        response = self._client.get('/copyfiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        copyfiles = response.data
        self.assertEqual(len(copyfiles["results"]), 1)
        copy1 = copyfiles["results"][0]
        self.assertEqual(copy1["name"], "Copy1")

    def test_admin_view(self):
        self._asAdmin()
        response = self._client.get('/copyfiles/%d/' % self._copyFile.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        copy1 = response.data
        self.assertEqual(copy1["name"], "Copy1")

    def test_user_create(self):
        self._asJaneDoe()
        new_copy = {"name": "Copy2",
                    "equipment": self._equipmentSequencer.name,
                    "copy_from_prefix": "jdprefix",
                    "copy_to_prefix": "jdpostfix",
                    "is_enabled": False,
                    "locations": [{"copy_from": "joe",
                                   "copy_to": "bloggs"}]}
        response = self._client.post("/copyfiles/", new_copy, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(CopyFileDriver.objects.count(), 2)
        self.assertIs(CopyFileDriver.objects.filter(name="Copy2").exists(), True)
        copy2 = CopyFileDriver.objects.get(name="Copy2")
        self.assertEqual(copy2.equipment, self._equipmentSequencer)
        self.assertEqual(copy2.copy_from_prefix, "jdprefix")
        self.assertEqual(copy2.copy_to_prefix, "jdpostfix")
        self.assertIs(copy2.is_enabled, False)
        self._asJoeBloggs()
        response = self._client.get('/copyfiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        copyfiles = response.data
        self.assertEqual(len(copyfiles["results"]), 2)

    def test_admin_create(self):
        self._asAdmin()
        new_copy = {"name": "Copy2",
                    "equipment": self._equipmentSequencer.name,
                    "copy_from_prefix": "jdprefix",
                    "copy_to_prefix": "jdpostfix",
                    "is_enabled": False,
                    "locations": [{"copy_from": "joe",
                                   "copy_to": "bloggs"}]}
        response = self._client.post("/copyfiles/", new_copy, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(CopyFileDriver.objects.count(), 2)
        self.assertIs(CopyFileDriver.objects.filter(name="Copy2").exists(), True)
        copy2 = CopyFileDriver.objects.get(name="Copy2")
        self.assertEqual(copy2.equipment, self._equipmentSequencer)
        self.assertEqual(copy2.copy_from_prefix, "jdprefix")
        self.assertEqual(copy2.copy_to_prefix, "jdpostfix")
        self.assertIs(copy2.is_enabled, False)
        self.assertEqual(copy2.locations.count(), 1)
        cfp = copy2.locations.all()[0]
        self.assertEqual(cfp.copy_from, "joe")
        self.assertEqual(cfp.copy_to, "bloggs")
        self._asJoeBloggs()
        response = self._client.get('/copyfiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        copyfiles = response.data
        self.assertEqual(len(copyfiles["results"]), 2)

    def test_user_edit(self):
        self._asJaneDoe()
        updated_copy = {"name": "Copy2",
                        "equipment": self._equipmentSequencer.name,
                        "copy_from_prefix": "jdprefix",
                        "copy_to_prefix": "jdpostfix",
                        "is_enabled": False,
                        "locations": [{"copy_from": "joe",
                                       "copy_to": "bloggs"}]}
        response = self._client.patch("/copyfiles/%d/" % self._copyFile.id,
                                      updated_copy, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(CopyFileDriver.objects.filter(name="Copy2").exists(), True)
        copy1 = CopyFileDriver.objects.get(name="Copy2")
        self.assertEqual(copy1.copy_from_prefix, "jdprefix")
        self.assertEqual(copy1.copy_to_prefix, "jdpostfix")
        self.assertIs(copy1.is_enabled, False)
        self.assertEqual(copy1.locations.count(), 1)
        cfp = copy1.locations.all()[0]
        self.assertEqual(cfp.copy_from, "joe")
        self.assertEqual(cfp.copy_to, "bloggs")

    def test_admin_edit(self):
        self._asAdmin()
        updated_copy = {"name": "Copy2",
                        "equipment": self._equipmentSequencer.name,
                        "copy_from_prefix": "jdprefix",
                        "copy_to_prefix": "jdpostfix",
                        "is_enabled": False,
                        "locations": [{"copy_from": "joe",
                                       "copy_to": "bloggs"}]}
        response = self._client.patch("/copyfiles/%d/" % self._copyFile.id,
                                      updated_copy, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(CopyFileDriver.objects.filter(name="Copy2").exists(), True)
        copy1 = CopyFileDriver.objects.get(name="Copy2")
        self.assertEqual(copy1.copy_from_prefix, "jdprefix")
        self.assertEqual(copy1.copy_to_prefix, "jdpostfix")
        self.assertIs(copy1.is_enabled, False)
        self.assertEqual(copy1.locations.count(), 1)
        cfp = copy1.locations.all()[0]
        self.assertEqual(cfp.copy_from, "joe")
        self.assertEqual(cfp.copy_to, "bloggs")

    def test_user_delete(self):
        self._asJoeBloggs()
        response = self._client.delete("/copyfiles/%d/" % self._copyFile.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(CopyFileDriver.objects.filter(name="Copy1").exists(), False)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete("/copyfiles/%d/" % self._copyFile.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(CopyFileDriver.objects.filter(name="Copy1").exists(), False)

    def test_fetch(self):
        # Create temp file to copy
        file = open(os.path.join(self._copyFile.copy_from_prefix,
                                 "%sbigFileXYZA" % tempfile.gettempprefix()), 'w')
        file.write("Lots of interesting stuff")
        file.close()
        # Perform copy
        interpolate_dict = {"project_identifier": tempfile.gettempprefix(),
                            "product_identifier": "bigFile",
                            "run_identifier": "XYZ"}
        result_paths = self._copyFile.fetch(interpolate_dict=interpolate_dict)
        # Test copied file exists and DataFile matches
        self.assertEqual(len(result_paths), 1)
        df = result_paths[0]
        self.assertEqual(df.file_name, "%sbigFileXYZB" % tempfile.gettempprefix())
        self.assertEqual(df.location, os.path.join(tempfile.gettempdir(),
                                                   "%sbigFileXYZB" % tempfile.gettempprefix()))
        self.assertEqual(df.equipment, self._equipmentSequencer)
        self.assertIs(filecmp.cmp(
            os.path.join(tempfile.gettempdir(), "%sbigFileXYZA" % tempfile.gettempprefix()),
            os.path.join(tempfile.gettempdir(), "%sbigFileXYZB" % tempfile.gettempprefix())), True)
        # Clean up
        os.remove(os.path.join(tempfile.gettempdir(), "%sbigFileXYZA" % tempfile.gettempprefix()))
        os.remove(os.path.join(tempfile.gettempdir(), "%sbigFileXYZB" % tempfile.gettempprefix()))
