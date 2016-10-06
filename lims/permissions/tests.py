from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status


class PermissionTestCase(LoggedInTestCase):
    def setUp(self):
        super(PermissionTestCase, self).setUp()
        self._changeEquipPermission = Permission.objects.get(name="Can change equipment")

    def test_presets(self):
        self.assertIs(Permission.objects.filter(name="Can change equipment").exists(), True)
        self.assertEqual(Permission.objects.get(name="Can change equipment").codename,
                         "change_equipment")

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/permissions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/permissions/%d/' % self._changeEquipPermission.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/permissions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/permissions/%d/' % self._changeEquipPermission.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/permissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions = response.data
        self.assertEqual(permissions["meta"]["count"], Permission.objects.count())

    def test_user_view_any(self):
        self._asJoeBloggs()
        response = self._client.get('/permissions/%d/' % self._changeEquipPermission.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permission1 = response.data
        self.assertEqual(permission1["name"], "Can change equipment")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/permissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions = response.data
        self.assertEqual(permissions["meta"]["count"], Permission.objects.count())

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/permissions/%d/' % self._changeEquipPermission.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permission1 = response.data
        self.assertEqual(permission1["name"], "Can change equipment")

    def test_user_create(self):
        self._asJaneDoe()
        new_permission = {"name": "Test permission", "codename": "test_permission",
                          "content_type": ContentType.objects.get(model="equipment").id}
        response = self._client.post("/permissions/", new_permission, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIs(Permission.objects.filter(name="Test permission").exists(), False)

    def test_admin_create(self):
        self._asAdmin()
        new_permission = {"name": "Test permission", "codename": "test_permission",
                          "content_type": ContentType.objects.get(model="equipment").id}
        response = self._client.post("/permissions/", new_permission, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIs(Permission.objects.filter(name="Test permission").exists(), False)

    def test_user_edit_any(self):
        self._asJaneDoe()
        updated_permission = {"codename": "silly_test"}
        response = self._client.patch("/permissions/%d/" % self._changeEquipPermission.id,
                                      updated_permission, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        permission1 = Permission.objects.get(name="Can change equipment")
        self.assertEqual(permission1.codename, "change_equipment")

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_permission = {"codename": "silly_test"}
        response = self._client.patch("/permissions/%d/" % self._changeEquipPermission.id,
                                      updated_permission, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_delete_any(self):
        self._asJoeBloggs()
        response = self._client.delete("/permissions/%d/" % self._changeEquipPermission.id)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIs(Permission.objects.filter(name="Can change equipment").exists(), True)

    def test_admin_delete_any(self):
        # Others not permitted
        self._asAdmin()
        response = self._client.delete("/permissions/%d/" % self._changeEquipPermission.id)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIs(Permission.objects.filter(name="Can change equipment").exists(), True)
