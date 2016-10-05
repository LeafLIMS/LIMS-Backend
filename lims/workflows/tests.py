from django.contrib.auth.models import Permission, Group
from rest_framework import status
from lims.shared.loggedintestcase import LoggedInTestCase
from .models import Workflow, Run, RunLabware, TaskTemplate, \
    CalculationFieldTemplate, InputFieldTemplate, \
    VariableFieldTemplate, OutputFieldTemplate, StepFieldTemplate, StepFieldProperty
from lims.datastore.models import DataEntry
from lims.filetemplate.models import FileTemplate, FileTemplateField
from lims.inventory.models import Location, Item, ItemType, AmountMeasure, ItemTransfer
from lims.equipment.models import Equipment
from .views import ViewPermissionsMixin
from lims.projects.models import Project, Order, Product, ProductStatus
from lims.shared.models import Organism
import json
from lims.inventory.serializers import ItemTransferPreviewSerializer
from lims.datastore.serializers import DataEntrySerializer
from lims.drivers.models import CopyFileDriver, CopyFilePath
import os
import filecmp
import tempfile


class WorkflowTestCase(LoggedInTestCase):
    def setUp(self):
        super(WorkflowTestCase, self).setUp()

        self._inputTempl = \
            FileTemplate.objects.create(name="InputTemplate1",
                                        file_for="input")
        FileTemplateField.objects.create(name="ID1Field1",
                                         required=True,
                                         is_identifier=True,
                                         template=self._inputTempl)
        FileTemplateField.objects.create(name="1Field1",
                                         required=False,
                                         is_identifier=False,
                                         template=self._inputTempl)
        self._outputTempl = \
            FileTemplate.objects.create(name="InputTemplate2",
                                        file_for="input")
        FileTemplateField.objects.create(name="ID2Field1",
                                         required=True,
                                         is_identifier=True,
                                         template=self._outputTempl)
        FileTemplateField.objects.create(name="ID2Field2",
                                         required=True,
                                         is_identifier=True,
                                         template=self._outputTempl)

        self._prodinput = ItemType.objects.create(name="ExampleStuff", parent=None)
        self._labware = ItemType.objects.create(name="ExampleLabware", parent=None)
        self._millilitre = AmountMeasure.objects.create(name="Millilitre", symbol="ml")
        self._location = Location.objects.create(name="Bench", code="B1")
        self._equipmentSequencer = Equipment.objects.create(name="Sequencer",
                                                            location=self._location,
                                                            status="active", can_reserve=True)

        self._task1 = TaskTemplate.objects.create(name="TaskTempl1",
                                                  description="First",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task1.capable_equipment.add(self._equipmentSequencer)
        self._task1.input_files.add(self._inputTempl)
        self._task1.output_files.add(self._outputTempl)
        self._task2 = TaskTemplate.objects.create(name="TaskTempl2",
                                                  description="Second",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task2.capable_equipment.add(self._equipmentSequencer)
        self._task2.input_files.add(self._inputTempl)
        self._task2.output_files.add(self._outputTempl)
        self._task3 = TaskTemplate.objects.create(name="TaskTempl3",
                                                  description="Third",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task3.capable_equipment.add(self._equipmentSequencer)
        self._task3.input_files.add(self._inputTempl)
        self._task3.output_files.add(self._outputTempl)
        self._task4 = TaskTemplate.objects.create(name="TaskTempl4",
                                                  description="Fourth",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task4.capable_equipment.add(self._equipmentSequencer)
        self._task4.input_files.add(self._inputTempl)
        self._task4.output_files.add(self._outputTempl)

        self._workflow1 = Workflow.objects.create(name="Workflow1",
                                                  order='%d,%d' % (self._task1.id, self._task2.id),
                                                  created_by=self._joeBloggs)
        self._workflow2 = Workflow.objects.create(name="Workflow2", order='%d,%d,%d' % (
            self._task1.id, self._task3.id, self._task4.id), created_by=self._janeDoe)
        self._workflow3 = Workflow.objects.create(name="Workflow3", order='%d,%d,%d' % (
            self._task3.id, self._task2.id, self._task1.id), created_by=self._janeDoe)

        # Joe can see and edit workflow 1, and see item 2 but not edit it. No access to 3.
        # Jane can see and edit items 3+2, and see item 1 but not edit it.
        ViewPermissionsMixin().assign_permissions(instance=self._workflow1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._workflow2,
                                                  permissions={"joe_group": "r",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._workflow3,
                                                  permissions={"jane_group": "rw"})

        # We also have to give Joe and Jane permission to view, change and delete items in
        # general.
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="add_workflow"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="view_workflow"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="change_workflow"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="delete_workflow"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="add_workflow"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_workflow"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="change_workflow"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="delete_workflow"))

    def test_presets(self):
        self.assertEqual(Workflow.objects.count(), 3)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(w.created_by, self._joeBloggs)
        self.assertEqual(w.order, '%d,%d' % (self._task1.id, self._task2.id))
        self.assertEqual(w.get_tasks(), [self._task1, self._task2])
        w = Workflow.objects.get(name="Workflow2")
        self.assertEqual(w.created_by, self._janeDoe)
        self.assertEqual(w.order, '%d,%d,%d' % (self._task1.id, self._task3.id, self._task4.id))
        self.assertEqual(w.get_tasks(), [self._task1, self._task3, self._task4])
        w = Workflow.objects.get(name="Workflow3")
        self.assertEqual(w.created_by, self._janeDoe)
        self.assertEqual(w.order, '%d,%d,%d' % (self._task3.id, self._task2.id, self._task1.id))
        self.assertEqual(w.get_tasks(), [self._task3, self._task2, self._task1])

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/workflows/%d/' % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/workflows/%d/' % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see items his group can see
        self._asJoeBloggs()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        w = wflows["results"][0]
        self.assertEqual(w["name"], "Workflow1")

    def test_user_list_group(self):
        # Jane can see all four because her group permissions permit this
        self._asJaneDoe()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 3)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/workflows/%d/' % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = response.data
        self.assertEqual(w["name"], "Workflow1")

    def test_user_view_other(self):
        # Jane's item 4 is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/workflows/%d/' % self._workflow3.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's items 1+2
        self._asJaneDoe()
        response = self._client.get('/workflows/%d/' % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = response.data
        self.assertEqual(w["name"], "Workflow1")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 3)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/workflows/%d/' % self._workflow2.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = response.data
        self.assertEqual(w["name"], "Workflow2")

    def test_user_create_own(self):
        self._asJaneDoe()
        new_wflow = {"name": "Workflow4",
                     "order": '%d,%d' % (self._task1.id, self._task2.id),
                     "created_by": self._janeDoe.id,
                     "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/workflows/", new_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Workflow.objects.count(), 4)
        self.assertIs(Workflow.objects.filter(name="Workflow4").exists(), True)
        w = Workflow.objects.get(name="Workflow4")
        self.assertEqual(w.created_by, self._janeDoe)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        self._asJaneDoe()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 4)

    def test_admin_create_any(self):
        # Admin should be able to create a set for someone else
        self._asAdmin()
        new_wflow = {"name": "Workflow4",
                     "order": '%d,%d' % (self._task1.id, self._task2.id),
                     "created_by": self._janeDoe.id,
                     "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/workflows/", new_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Workflow.objects.count(), 4)
        self.assertIs(Workflow.objects.filter(name="Workflow4").exists(), True)
        w = Workflow.objects.get(name="Workflow4")
        self.assertEqual(w.created_by, self._adminUser)  # created_by always overridden

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        self._asJaneDoe()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 4)

    def test_user_edit_own(self):
        self._asJoeBloggs()
        update_wflow = {"name": "Update"}
        response = self._client.patch("/workflows/%d/" % self._workflow1.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Workflow.objects.filter(name="Workflow1").exists(), False)
        self.assertIs(Workflow.objects.filter(name="Update").exists(), True)

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's item 4
        self._asJoeBloggs()
        update_wflow = {"name": "Update"}
        response = self._client.patch("/workflows/%d/" % self._workflow3.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Workflow.objects.filter(name="Workflow3").exists(), True)
        self.assertIs(Workflow.objects.filter(name="Update").exists(), False)

    def test_user_edit_other_readonly(self):
        # Joe can see but not edit Jane's item 3
        self._asJoeBloggs()
        update_wflow = {"name": "Update"}
        response = self._client.patch("/workflows/%d/" % self._workflow2.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Workflow.objects.filter(name="Workflow2").exists(), True)
        self.assertIs(Workflow.objects.filter(name="Update").exists(), False)

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's item 1 first so she can edit it
        ViewPermissionsMixin().assign_permissions(instance=self._workflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        update_wflow = {"name": "Update"}
        response = self._client.patch("/workflows/%d/" % self._workflow1.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Workflow.objects.filter(name="Workflow1").exists(), False)
        self.assertIs(Workflow.objects.filter(name="Update").exists(), True)

    def test_admin_edit_any(self):
        self._asAdmin()
        update_wflow = {"name": "Update"}
        response = self._client.patch("/workflows/%d/" % self._workflow1.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Workflow.objects.filter(name="Workflow1").exists(), False)
        self.assertIs(Workflow.objects.filter(name="Update").exists(), True)

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/workflows/%d/" % self._workflow3.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Workflow.objects.filter(name="Workflow3").exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/workflows/%d/" % self._workflow3.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Workflow.objects.filter(name="Workflow3").exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/workflows/%d/" % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Workflow.objects.filter(name="Workflow1").exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._workflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/workflows/%d/" % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Workflow.objects.filter(name="Workflow1").exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/workflows/%d/" % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Workflow.objects.filter(name="Workflow1").exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own sets
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch(
            "/workflows/%d/set_permissions/" % self._workflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        permissions = {"jane_group": "r"}
        response = self._client.patch(
            "/workflows/%d/set_permissions/" % self._workflow3.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        w = Workflow.objects.get(name="Workflow3")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch(
            "/workflows/%d/set_permissions/" % self._workflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._workflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/workflows/%d/set_permissions/" % self._workflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_admin_set_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/workflows/%d/set_permissions/" % self._workflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_set_permissions_invalid_group(self):
        # An invalid group should throw a 400 data error
        self._asAdmin()
        permissions = {"jim_group": "r"}
        response = self._client.patch(
            "/workflows/%d/set_permissions/" % self._workflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch(
            "/workflows/%d/set_permissions/" % self._workflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the permission wasn't changed accidentally in the process
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/workflows/%d/remove_permissions/?groups=joe_group" % self._workflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's item 4
        self._asJoeBloggs()
        response = self._client.delete(
            "/workflows/%d/remove_permissions/?groups=jane_group" % self._workflow3.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        w = Workflow.objects.get(name="Workflow3")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's item 1
        self._asJaneDoe()
        response = self._client.delete(
            "/workflows/%d/remove_permissions/?groups=joe_group" % self._workflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._workflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/workflows/%d/remove_permissions/?groups=joe_group" % self._workflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/workflows/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._workflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Workflow.objects.get(name="Workflow1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), None)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_remove_permissions_invalid_group(self):
        # An invalid group name should fail quietly - we don't care if permissions can't be
        # removed as the end result is the same, i.e. that group can't access anything
        self._asAdmin()
        response = self._client.delete(
            "/workflows/%d/remove_permissions/?groups=jim_group" %
            self._workflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_workflow_taskdetails_validpos(self):
        self._asJoeBloggs()
        response = self._client.get(
            '/workflows/%d/task_details/?position=%d' % (self._workflow1.id, 1))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "TaskTempl2")

    def test_workflow_taskdetails_nopos(self):
        self._asJoeBloggs()
        response = self._client.get('/workflows/%d/task_details/' % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Please provide a task position")

    def test_workflow_taskdetails_invalidpos(self):
        self._asJoeBloggs()
        response = self._client.get(
            '/workflows/%d/task_details/?position=%d' % (self._workflow1.id, 99))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid position")

    def test_workflow_taskdetails_invalidtask(self):
        self._asJoeBloggs()
        self._task2.delete()
        response = self._client.get(
            '/workflows/%d/task_details/?position=%d' % (self._workflow1.id, 1))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Task does not exist")

    def test_workflow_tasks(self):
        self._asJoeBloggs()
        response = self._client.get('/workflows/%d/tasks/' % self._workflow1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["tasks"]
        self.assertEqual(len(t), 2)
        self.assertEqual(t[0]["name"], "TaskTempl1")
        self.assertEqual(t[1]["name"], "TaskTempl2")


class TaskTestCase(LoggedInTestCase):
    def setUp(self):
        super(TaskTestCase, self).setUp()

        self._inputTempl = \
            FileTemplate.objects.create(name="InputTemplate1",
                                        file_for="input")
        FileTemplateField.objects.create(name="ID1Field1",
                                         required=True,
                                         is_identifier=True,
                                         template=self._inputTempl)
        FileTemplateField.objects.create(name="1Field1",
                                         required=False,
                                         is_identifier=False,
                                         template=self._inputTempl)
        self._outputTempl = \
            FileTemplate.objects.create(name="InputTemplate2",
                                        file_for="input")
        FileTemplateField.objects.create(name="ID2Field1",
                                         required=True,
                                         is_identifier=True,
                                         template=self._outputTempl)
        FileTemplateField.objects.create(name="ID2Field2",
                                         required=True,
                                         is_identifier=True,
                                         template=self._outputTempl)
        self._equipTempl = \
            FileTemplate.objects.create(name="EquipTemplate",
                                        file_for="input")
        FileTemplateField.objects.create(name="ID3Field1",
                                         required=True,
                                         is_identifier=True,
                                         template=self._equipTempl)
        FileTemplateField.objects.create(name="ID3Field2",
                                         required=True,
                                         is_identifier=True,
                                         template=self._equipTempl)

        self._prodinput = ItemType.objects.create(name="ExampleStuff", parent=None)
        self._labware = ItemType.objects.create(name="ExampleLabware", parent=None)
        self._millilitre = AmountMeasure.objects.create(name="Millilitre", symbol="ml")
        self._location = Location.objects.create(name="Bench", code="B1")
        self._equipmentSequencer = Equipment.objects.create(name="Sequencer",
                                                            location=self._location,
                                                            status="active", can_reserve=True)

        self._task1 = TaskTemplate.objects.create(name="TaskTempl1",
                                                  description="First",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task1.capable_equipment.add(self._equipmentSequencer)
        self._task1.input_files.add(self._inputTempl)
        self._task1.output_files.add(self._outputTempl)
        self._task1.equipment_files.add(self._equipTempl)
        self._task2 = TaskTemplate.objects.create(name="TaskTempl2",
                                                  description="Second",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task2.capable_equipment.add(self._equipmentSequencer)
        self._task2.input_files.add(self._inputTempl)
        self._task2.output_files.add(self._outputTempl)
        self._task2.equipment_files.add(self._equipTempl)
        self._task3 = TaskTemplate.objects.create(name="TaskTempl3",
                                                  description="Third",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task3.capable_equipment.add(self._equipmentSequencer)
        self._task3.input_files.add(self._inputTempl)
        self._task3.output_files.add(self._outputTempl)
        self._task3.equipment_files.add(self._equipTempl)

        # Joe can see and edit workflow 1, and see item 2 but not edit it. No access to 3.
        # Jane can see and edit items 3+2, and see item 1 but not edit it.
        ViewPermissionsMixin().assign_permissions(instance=self._task1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._task2,
                                                  permissions={"joe_group": "r",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._task3,
                                                  permissions={"jane_group": "rw"})

        # We also have to give Joe and Jane permission to view, change and delete items in
        # general.
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="add_tasktemplate"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="view_tasktemplate"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="change_tasktemplate"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="delete_tasktemplate"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="add_tasktemplate"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_tasktemplate"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="change_tasktemplate"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="delete_tasktemplate"))

        # And step field templates for taskfield requests
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="add_stepfieldtemplate"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="view_stepfieldtemplate"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="change_stepfieldtemplate"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="delete_stepfieldtemplate"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="add_stepfieldtemplate"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="view_stepfieldtemplate"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="change_stepfieldtemplate"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="delete_stepfieldtemplate"))

    def test_presets(self):
        self.assertEqual(TaskTemplate.objects.count(), 3)
        t = TaskTemplate.objects.get(name="TaskTempl2")
        self.assertEqual(t.description, "Second")
        self.assertEqual(t.product_input, self._prodinput)
        self.assertEqual(t.product_input_amount, 1)
        self.assertEqual(t.product_input_measure, self._millilitre)
        self.assertEqual(t.labware, self._labware)
        self.assertEqual(t.created_by, self._joeBloggs)
        self.assertEqual(set(t.capable_equipment.all()), set([self._equipmentSequencer]))
        self.assertEqual(set(t.input_files.all()), set([self._inputTempl]))
        self.assertEqual(set(t.output_files.all()), set([self._outputTempl]))
        self.assertEqual(set(t.equipment_files.all()), set([self._equipTempl]))

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/tasks/%d/' % self._task1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/tasks/%d/' % self._task1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see items his group can see
        self._asJoeBloggs()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = response.data
        self.assertEqual(len(tasks["results"]), 2)
        t = tasks["results"][0]
        self.assertEqual(t["name"], "TaskTempl1")

    def test_user_list_group(self):
        # Jane can see all four because her group permissions permit this
        self._asJaneDoe()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = response.data
        self.assertEqual(len(tasks["results"]), 3)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/tasks/%d/' % self._task1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(t["name"], "TaskTempl1")

    def test_user_view_other(self):
        # Jane's item 4 is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/tasks/%d/' % self._task3.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's items 1+2
        self._asJaneDoe()
        response = self._client.get('/tasks/%d/' % self._task1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(t["name"], "TaskTempl1")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = response.data
        self.assertEqual(len(tasks["results"]), 3)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/tasks/%d/' % self._task2.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(t["name"], "TaskTempl2")

    def test_user_create_own(self):
        self._asJaneDoe()
        new_task = {"name": "NewTask",
                    "description": "Description",
                    "product_input": self._prodinput.name,
                    "product_input_amount": 1,
                    "product_input_measure": self._millilitre.symbol,
                    "labware": self._labware.name,
                    "created_by": self._janeDoe.id,
                    "capable_equipment": [self._equipmentSequencer.name],
                    "input_files": [self._inputTempl.name],
                    "output_files": [self._outputTempl.name],
                    "equipment_files": [self._equipTempl.name],
                    "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/tasks/", new_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(TaskTemplate.objects.count(), 4)
        self.assertIs(TaskTemplate.objects.filter(name="NewTask").exists(), True)
        t = TaskTemplate.objects.get(name="NewTask")
        self.assertEqual(t.description, "Description")
        self.assertEqual(t.created_by, self._janeDoe)
        self.assertEqual(set(t.capable_equipment.all()), set([self._equipmentSequencer]))
        self.assertEqual(set(t.input_files.all()), set([self._inputTempl]))
        self.assertEqual(set(t.output_files.all()), set([self._outputTempl]))
        self.assertEqual(set(t.equipment_files.all()), set([self._equipTempl]))

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        self._asJaneDoe()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 4)

    def test_admin_create_any(self):
        # Admin should be able to create a set for someone else
        self._asAdmin()
        new_task = {"name": "NewTask",
                    "description": "Description",
                    "product_input": self._prodinput.name,
                    "product_input_amount": 1,
                    "product_input_measure": self._millilitre.symbol,
                    "labware": self._labware.name,
                    "created_by": self._janeDoe.id,
                    "capable_equipment": [self._equipmentSequencer.name],
                    "input_files": [self._inputTempl.name],
                    "output_files": [self._outputTempl.name],
                    "equipment_files": [self._equipTempl.name],
                    "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/tasks/", new_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(TaskTemplate.objects.count(), 4)
        self.assertIs(TaskTemplate.objects.filter(name="NewTask").exists(), True)
        t = TaskTemplate.objects.get(name="NewTask")
        self.assertEqual(t.description, "Description")
        self.assertEqual(t.created_by, self._adminUser)  # created_by always overridden
        self.assertEqual(t.capable_equipment.all()[0], self._equipmentSequencer)
        self.assertEqual(t.input_files.all()[0], self._inputTempl)
        self.assertEqual(t.output_files.all()[0], self._outputTempl)
        self.assertEqual(t.equipment_files.all()[0], self._equipTempl)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        self._asJaneDoe()
        response = self._client.get('/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 4)

    def test_user_edit_own(self):
        self._asJoeBloggs()
        updated_task = {"description": "Update"}
        response = self._client.patch("/tasks/%d/" % self._task1.id,
                                      updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(TaskTemplate.objects.filter(description="First").exists(), False)
        self.assertIs(TaskTemplate.objects.filter(description="Update").exists(), True)

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's item 4
        self._asJoeBloggs()
        updated_task = {"description": "Update"}
        response = self._client.patch("/tasks/%d/" % self._task3.id,
                                      updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(TaskTemplate.objects.filter(description="Third").exists(), True)
        self.assertIs(TaskTemplate.objects.filter(description="Update").exists(), False)

    def test_user_edit_other_readonly(self):
        # Joe can see but not edit Jane's item 3
        self._asJoeBloggs()
        updated_task = {"description": "Update"}
        response = self._client.patch("/tasks/%d/" % self._task2.id,
                                      updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(TaskTemplate.objects.filter(description="Second").exists(), True)
        self.assertIs(TaskTemplate.objects.filter(description="Update").exists(), False)

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's item 1 first so she can edit it
        ViewPermissionsMixin().assign_permissions(instance=self._task1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        updated_task = {"description": "Update"}
        response = self._client.patch("/tasks/%d/" % self._task1.id,
                                      updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(TaskTemplate.objects.filter(description="First").exists(), False)
        self.assertIs(TaskTemplate.objects.filter(description="Update").exists(), True)

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_task = {"description": "Update"}
        response = self._client.patch("/tasks/%d/" % self._task1.id,
                                      updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(TaskTemplate.objects.filter(description="First").exists(), False)
        self.assertIs(TaskTemplate.objects.filter(description="Update").exists(), True)

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/tasks/%d/" % self._task3.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(TaskTemplate.objects.filter(name="TaskTempl3").exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/tasks/%d/" % self._task3.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(TaskTemplate.objects.filter(name="TaskTempl3").exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/tasks/%d/" % self._task1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(TaskTemplate.objects.filter(name="TaskTempl1").exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._task1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/tasks/%d/" % self._task1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(TaskTemplate.objects.filter(name="TaskTempl1").exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/tasks/%d/" % self._task1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(TaskTemplate.objects.filter(name="TaskTempl1").exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own sets
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch(
            "/tasks/%d/set_permissions/" % self._task1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        permissions = {"jane_group": "r"}
        response = self._client.patch(
            "/tasks/%d/set_permissions/" % self._task3.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        t = TaskTemplate.objects.get(name="TaskTempl3")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch(
            "/tasks/%d/set_permissions/" % self._task1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._task1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/tasks/%d/set_permissions/" % self._task1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_admin_set_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/tasks/%d/set_permissions/" % self._task1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_set_permissions_invalid_group(self):
        # An invalid group should throw a 400 data error
        self._asAdmin()
        permissions = {"jim_group": "r"}
        response = self._client.patch(
            "/tasks/%d/set_permissions/" % self._task1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch(
            "/tasks/%d/set_permissions/" % self._task1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the permission wasn't changed accidentally in the process
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/tasks/%d/remove_permissions/?groups=joe_group" % self._task1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's item 4
        self._asJoeBloggs()
        response = self._client.delete(
            "/tasks/%d/remove_permissions/?groups=jane_group" % self._task3.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        t = TaskTemplate.objects.get(name="TaskTempl3")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's item 1
        self._asJaneDoe()
        response = self._client.delete(
            "/tasks/%d/remove_permissions/?groups=joe_group" % self._task1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._task1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/tasks/%d/remove_permissions/?groups=joe_group" % self._task1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/tasks/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._task1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = TaskTemplate.objects.get(name="TaskTempl1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="jane_group")), None)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=t,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_remove_permissions_invalid_group(self):
        # An invalid group name should fail quietly - we don't care if permissions can't be
        # removed as the end result is the same, i.e. that group can't access anything
        self._asAdmin()
        response = self._client.delete(
            "/tasks/%d/remove_permissions/?groups=jim_group" %
            self._task1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_task_store_labware_as(self):
        self.assertEqual(self._task1.store_labware_as(), "labware_identifier")

    def _setup_test_task_fields(self):
        # Set up some test fields on the task
        calc = "{input1}+{input2}*{output1]}/{variable1}*{prop1}+{product_input_amount}"
        self._calcField = CalculationFieldTemplate.objects.create(template=self._task3,
                                                                  label='calc1',
                                                                  description="Calculation field 1",
                                                                  calculation=calc)
        self._task3.calculation_fields.add(self._calcField)
        self._inputField1 = InputFieldTemplate.objects.create(template=self._task3,
                                                              label='input1',
                                                              description="Input field 1",
                                                              amount=1.0,
                                                              measure=self._millilitre,
                                                              lookup_type=self._prodinput,
                                                              from_input_file=False)
        self._inputField2 = InputFieldTemplate.objects.create(template=self._task3,
                                                              label='input2',
                                                              description="Input field 2",
                                                              amount=4.4,
                                                              measure=self._millilitre,
                                                              lookup_type=self._prodinput,
                                                              from_input_file=False)
        self._task3.input_fields.add(self._inputField1)
        self._task3.input_fields.add(self._inputField2)
        self._variableField = VariableFieldTemplate.objects.create(
            template=self._task1,
            label="variable1",
            description="Variable field 1",
            amount=3.3,
            measure=self._millilitre,
            measure_not_required=False)
        self._task3.variable_fields.add(self._variableField)
        self._outputField = OutputFieldTemplate.objects.create(template=self._task3,
                                                               label='output1',
                                                               description="Output field 1",
                                                               amount=9.6,
                                                               measure=self._millilitre,
                                                               lookup_type=self._prodinput)
        self._task3.output_fields.add(self._outputField)
        self._stepField = StepFieldTemplate.objects.create(template=self._task3,
                                                           label='step1',
                                                           description="Step field 1")
        self._stepFieldProperty = StepFieldProperty.objects.create(step=self._stepField,
                                                                   label='prop1',
                                                                   amount=9.6,
                                                                   measure=self._millilitre)
        self._stepField.properties.add(self._stepFieldProperty)
        self._task3.step_fields.add(self._stepField)
        self._task3.save()

    def _setup_test_task_recalculation(self):
        return {"id": self._task1.id,
                "product_input_measure": self._millilitre.symbol,
                "product_input_amount": 5,
                "product_input": self._prodinput.name,
                "input_files": [self._inputTempl.name],
                "output_files": [self._outputTempl.name],
                "equipment_files": [self._equipTempl.name],
                "labware": self._labware.name,
                "store_labware_as": "labware_identifier",
                "capable_equipment": [self._equipmentSequencer.name],
                "name": "NewTask",
                "assign_groups": {"jane_group": "rw"},
                "input_fields": [{"measure": self._millilitre.symbol,
                                  "lookup_type": self._prodinput.name, "label": "input1",
                                  "amount": 6.2, "template": self._task3.id,
                                  "calculation_used": self._calcField.id,
                                  "from_calculation": False},
                                 {"measure": self._millilitre.symbol,
                                  "lookup_type": self._prodinput.name, "label": "input2",
                                  "amount": 4.3, "template": self._task3.id,
                                  "calculation_used": self._calcField.id,
                                  "from_calculation": False}],
                "step_fields": [
                    {"label": "step1", "template": self._task3.id,
                     "properties": [{"id": self._stepFieldProperty.id,
                                     "measure": self._millilitre.symbol,
                                     "label": "prop1", "amount": 9.9,
                                     "calculation_used": self._calcField.id,
                                     "from_calculation": False}]}],
                "variable_fields": [
                    {"measure": self._millilitre.symbol, "label": "variable1",
                     "amount": 8.4, "template": self._task3.id}],
                "output_fields": [{"measure": self._millilitre.symbol,
                                   "lookup_type": self._prodinput.name, "label": "output1",
                                   "amount": 9.6, "template": self._task3.id,
                                   "calculation_used": self._calcField.id,
                                   "from_calculation": False}],
                "calculation_fields": [{"id": self._calcField.id,
                                        "label": "calc1",
                                        "calculation": ("{input1}"
                                                        "+{input2}"
                                                        "/{variable1}"
                                                        "*{prop1}"
                                                        "+{product_input_amount}"),
                                        "template": self._task3.id}],
                "created_by": self._janeDoe.username}

    def test_user_recalculate_nonread_task(self):
        self._setup_test_task_fields()
        updated_task = self._setup_test_task_recalculation()
        self._asJoeBloggs()
        response = self._client.post("/tasks/%d/recalculate/" % self._task3.id,
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_recalculate_readonly_task(self):
        self._setup_test_task_fields()
        updated_task = self._setup_test_task_recalculation()
        self._asJaneDoe()
        response = self._client.post("/tasks/%d/recalculate/" % self._task1.id,
                                     # ID mismatch doesn't matter as won't get that far
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_recalculate_readwrite_task(self):
        self._setup_test_task_fields()
        updated_task = self._setup_test_task_recalculation()
        self._asJaneDoe()
        response = self._client.post("/tasks/%d/recalculate/" % self._task3.id,
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["calculation_fields"][0]["result"], 16.267857142857142)

    def test_admin_recalculate_task(self):
        self._setup_test_task_fields()
        updated_task = self._setup_test_task_recalculation()
        self._asAdmin()
        response = self._client.post("/tasks/%d/recalculate/" % self._task3.id,
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["calculation_fields"][0]["result"], 16.267857142857142)

    def test_user_listall_taskfield_readonly(self):
        self._setup_test_task_fields()
        # Make Jane temporarily readonly on her task
        ViewPermissionsMixin().assign_permissions(instance=self._task3,
                                                  permissions={"jane_group": "r"})
        self._asJaneDoe()
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["results"]
        # TODO This test fails because Jane - who is r-only for TaskTemplate 'task3' - should
        # be able to see the StepFieldTemplate associated with that task, but the
        # system is not returning it because it is checking Field permissions not Template ones.
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._stepField.label)

    def test_user_listall_taskfield_nonread(self):
        self._setup_test_task_fields()
        self._asJoeBloggs()
        # Joe should see none as all on Jane's
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["results"]
        self.assertEqual(len(t), 0)

    def test_user_listall_taskfield_readwrite(self):
        self._setup_test_task_fields()
        self._asJaneDoe()
        ViewPermissionsMixin().assign_permissions(self._stepField, {'jane_group': 'rw'})
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TODO This test fails because Jane - who is r/w for TaskTemplate 'task3' - should
        # be able to see the StepFieldTemplate associated with that task, but the
        # system is not returning it because it is checking Field permissions not Template ones.
        t = response.data["results"]
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._stepField.label)

    def test_admin_listall_taskfield_any(self):
        self._setup_test_task_fields()
        self._asAdmin()
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["results"]
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._stepField.label)
        response = self._client.get('/taskfields/?type=%s' % "Input")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["results"]
        self.assertEqual(len(t), 2)
        self.assertEqual(t[0]["label"], self._inputField1.label)
        self.assertEqual(t[1]["label"], self._inputField2.label)
        response = self._client.get('/taskfields/?type=%s' % "Output")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["results"]
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._outputField.label)
        response = self._client.get('/taskfields/?type=%s' % "Variable")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["results"]
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._variableField.label)
        response = self._client.get('/taskfields/?type=%s' % "Calculation")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data["results"]
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._calcField.label)

    def test_user_create_taskfield_readonly(self):
        self._setup_test_task_fields()
        ViewPermissionsMixin().assign_permissions(instance=self._task3,
                                                  permissions={"jane_group": "r"})
        self._asJaneDoe()
        new_taskfield = {"template": self._task3.id,
                         "label": "step2",
                         "description": "Step field 2",
                         "measure": self._millilitre.symbol,
                         "amount": 5,
                         "lookup_type": self._prodinput.name}
        response = self._client.post('/taskfields/?type=%s' % "Step", new_taskfield)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # TODO the system currently allows Jane to create fields on this task even though she has
        # no write permissions to TaskTemplate 'task3'. It gives 201 when it should give 403
        # because she should be able to see but not edit the task this field is for.
        self.assertEqual(self._task3.step_fields.count(), 1)
        self.assertIs(self._task3.step_fields.filter(description="Step field 2").exists(), False)

    def test_user_create_taskfield_nonread(self):
        self._setup_test_task_fields()
        self._asJoeBloggs()
        new_taskfield = {"template": self._task3.id,
                         "label": "step2",
                         "description": "Step field 2",
                         "measure": self._millilitre.symbol,
                         "amount": 5,
                         "lookup_type": self._prodinput.name}
        response = self._client.post('/taskfields/?type=%s' % "Step", new_taskfield)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # TODO the system currently allows Joe to create fields on this task even though he has
        # no permissions at all on TaskTemplate 'task3'. It gives 201 when it should give 404
        # because he shouldn't even be able to see the task this field is for.
        self.assertEqual(self._task3.step_fields.count(), 1)
        self.assertIs(self._task3.step_fields.filter(description="Step field 2").exists(), False)

    def test_user_create_taskfield_readwrite(self):
        self._setup_test_task_fields()
        self._asJaneDoe()
        new_taskfield = {"template": self._task3.id,
                         "label": "step2",
                         "description": "Step field 2",
                         "amount": 9.6, "measure": self._millilitre.symbol}
        response = self._client.post('/taskfields/?type=%s' % "Step", new_taskfield)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self._task3.step_fields.count(), 2)
        self.assertIs(self._task3.step_fields.filter(description="Step field 2").exists(), True)

    def test_admin_create_taskfield_any(self):
        self._setup_test_task_fields()
        self._asAdmin()
        new_taskfield = {"template": self._task3.id,
                         "label": "step2",
                         "description": "Step field 2",
                         "amount": 9.6, "measure": self._millilitre.symbol}
        response = self._client.post('/taskfields/?type=%s' % "Step", new_taskfield)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self._task3.step_fields.count(), 2)
        self.assertIs(self._task3.step_fields.filter(description="Step field 2").exists(), True)

    def test_user_edit_taskfield_readonly(self):
        self._setup_test_task_fields()
        ViewPermissionsMixin().assign_permissions(instance=self._task3,
                                                  permissions={"jane_group": "r"})
        self._asJaneDoe()
        updated_taskfield = {"description": "Blah"}
        response = self._client.patch('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"),
                                      updated_taskfield)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # TODO This test fails because Jane - who is r-only for TaskTemplate 'task3' - should
        # be able to see and not edit the StepFieldTemplate associated with that task, but the
        # system is saying she can't see it at all (404) as opposed to see but not edit (403)

    def test_user_edit_taskfield_nonread(self):
        self._setup_test_task_fields()
        self._asJoeBloggs()
        updated_taskfield = {"description": "Blah"}
        response = self._client.patch('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"),
                                      updated_taskfield)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_edit_taskfield_readwrite(self):
        self._setup_test_task_fields()
        self._asJaneDoe()
        ViewPermissionsMixin().assign_permissions(self._stepField, {'jane_group': 'rw'})
        updated_taskfield = {"description": "Blah"}
        response = self._client.patch('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"),
                                      updated_taskfield)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TODO This test fails because Jane - who is r/w for TaskTemplate 'task3' - should
        # be able to see and edit the StepFieldTemplate associated with that task, but the
        # system is saying she can't see it at all (404) as opposed to edit it fine (200)
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), False)
        self.assertIs(self._task3.step_fields.filter(description="Blah").exists(), True)

    def test_admin_edit_taskfield_any(self):
        self._setup_test_task_fields()
        self._asAdmin()
        updated_taskfield = {"description": "Blah"}
        response = self._client.patch('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"),
                                      updated_taskfield)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), False)
        self.assertIs(self._task3.step_fields.filter(description="Blah").exists(), True)

    def test_user_delete_taskfield_readonly(self):
        self._setup_test_task_fields()
        ViewPermissionsMixin().assign_permissions(instance=self._task3,
                                                  permissions={"jane_group": "r"})
        self._asJaneDoe()
        response = self._client.delete('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # TODO This test fails because Jane has r-only permissions on TemplateTask 'task3' to which
        # this field belongs and therefore should be able to view but not edit this field, giving
        # a 403 if she tries to edit, but the system gives 404 saying she cannot even see it
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), True)

    def test_user_delete_taskfield_nonread(self):
        self._setup_test_task_fields()
        self._asJoeBloggs()
        response = self._client.delete('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), True)

    def test_user_delete_taskfield_readwrite(self):
        self._setup_test_task_fields()
        self._asJaneDoe()
        ViewPermissionsMixin().assign_permissions(self._stepField, {'jane_group': 'rw'})
        response = self._client.delete('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # TODO This test fails because Jane has r/w permissions on TemplateTask 'task3' to which
        # this field belongs and therefore should be able to delete this field, but the system
        # gives 404 saying she cannot even see it
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), False)

    def test_admin_delete_taskfield_any(self):
        self._setup_test_task_fields()
        self._asAdmin()
        response = self._client.delete('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), False)


class RunTestCase(LoggedInTestCase):
    def setUp(self):
        super(RunTestCase, self).setUp()

        self._inputTempl = \
            FileTemplate.objects.create(name="InputTemplate1",
                                        file_for="input")
        FileTemplateField.objects.create(name="prodID",
                                         required=True,
                                         is_identifier=True,
                                         template=self._inputTempl)
        FileTemplateField.objects.create(name="input2 identifier",
                                         required=True,
                                         is_identifier=True,
                                         template=self._inputTempl)
        FileTemplateField.objects.create(name="input2 amount",
                                         required=True,
                                         is_identifier=False,
                                         template=self._inputTempl)
        self._outputTempl = \
            FileTemplate.objects.create(name="InputTemplate2",
                                        file_for="input")
        FileTemplateField.objects.create(name="ID2Field1",
                                         required=True,
                                         is_identifier=True,
                                         template=self._outputTempl)
        FileTemplateField.objects.create(name="ID2Field2",
                                         required=True,
                                         is_identifier=True,
                                         template=self._outputTempl)
        self._equipTempl1 = \
            FileTemplate.objects.create(name="EquipTemplate1",
                                        file_for="input",
                                        use_inputs=True,
                                        total_inputs_only=False)
        for field in ["labware_amount", "input2.measure", "input2.inventory_identifier",
                      "input2.amount", "product_name", "equipment_choice", "input1.measure",
                      "input1.inventory_identifier", "input1.amount", "created_by",
                      "labware_identifier", "output1.lookup_type", "output1.amount", "task", "run",
                      "task_input.measure", "task_input.name", "task_input.amount"]:
            FileTemplateField.objects.create(name=field, required=False, is_identifier=False,
                                             template=self._equipTempl1)
        self._equipTempl2 = \
            FileTemplate.objects.create(name="EquipTemplate2",
                                        file_for="input",
                                        use_inputs=False,
                                        total_inputs_only=True)
        # TODO Need to fix TaskTemplate.data_to_output_file then implement appropriate fields here
        self._equipTempl3 = \
            FileTemplate.objects.create(name="EquipTemplate3",
                                        file_for="input",
                                        use_inputs=False,
                                        total_inputs_only=False)
        for field in ["labware_amount", "input2.measure", "input2.inventory_identifier",
                      "input2.amount", "product_name", "equipment_choice", "input1.measure",
                      "input1.inventory_identifier", "input1.amount", "created_by",
                      "labware_identifier", "output1.lookup_type", "output1.amount", "task", "run"]:
            FileTemplateField.objects.create(name=field, required=False, is_identifier=False,
                                             template=self._equipTempl3)

        self._prodinput = ItemType.objects.create(name="ExampleStuff", parent=None)
        self._labware = ItemType.objects.create(name="ExampleLabware", parent=None)
        self._millilitre = AmountMeasure.objects.create(name="Millilitre", symbol="ml")
        self._location = Location.objects.create(name="Lab", code="L1")
        self._location = Location.objects.create(name="Bench", code="B1")
        self._equipmentSequencer = Equipment.objects.create(name="Sequencer",
                                                            location=self._location,
                                                            status="active", can_reserve=True)
        self._tempfileDir = tempfile.gettempdir()
        self._copyFile = \
            CopyFileDriver.objects.create(name="Copy1",
                                          equipment=self._equipmentSequencer,
                                          copy_from_prefix=self._tempfileDir,
                                          copy_to_prefix=self._tempfileDir,
                                          is_enabled=True)
        self._tempfilePrefix = tempfile.gettempprefix()
        self._copyFilePath = \
            CopyFilePath.objects.create(
                driver=self._copyFile,
                copy_from="%s{run_identifier}A" % self._tempfilePrefix,
                copy_to="%s{run_identifier}B" % self._tempfilePrefix)
        self._copyFile.locations.add(self._copyFilePath)

        self._task1 = TaskTemplate.objects.create(name="TaskTempl1",
                                                  description="First",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task1.capable_equipment.add(self._equipmentSequencer)
        self._task1.input_files.add(self._inputTempl)
        self._task1.output_files.add(self._outputTempl)
        self._task1.equipment_files.add(self._equipTempl1)
        self._task2 = TaskTemplate.objects.create(name="TaskTempl2",
                                                  description="Second",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task2.capable_equipment.add(self._equipmentSequencer)
        self._task2.input_files.add(self._inputTempl)
        self._task2.output_files.add(self._outputTempl)
        self._task2.equipment_files.add(self._equipTempl1)
        self._task3 = TaskTemplate.objects.create(name="TaskTempl3",
                                                  description="Third",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task3.capable_equipment.add(self._equipmentSequencer)
        self._task3.input_files.add(self._inputTempl)
        self._task3.output_files.add(self._outputTempl)
        self._task3.equipment_files.add(self._equipTempl1)
        self._task3.equipment_files.add(self._equipTempl2)
        self._task3.equipment_files.add(self._equipTempl3)
        self._task4 = TaskTemplate.objects.create(name="TaskTempl4",
                                                  description="Fourth",
                                                  product_input=self._prodinput,
                                                  product_input_amount=1,
                                                  product_input_measure=self._millilitre,
                                                  labware=self._labware,
                                                  created_by=self._joeBloggs)
        self._task4.capable_equipment.add(self._equipmentSequencer)
        self._task4.input_files.add(self._inputTempl)
        self._task4.output_files.add(self._outputTempl)

        calc = "{input1}+{input2}*{output1]}/{variable1}*{prop1}+{product_input_amount}"
        self._calcField = CalculationFieldTemplate.objects.create(template=self._task3,
                                                                  label='calc1',
                                                                  description="Calculation field 1",
                                                                  calculation=calc)
        self._task3.calculation_fields.add(self._calcField)
        self._inputField1 = InputFieldTemplate.objects.create(template=self._task3,
                                                              label='input1',
                                                              description="Input field 1",
                                                              amount=1,
                                                              measure=self._millilitre,
                                                              lookup_type=self._prodinput,
                                                              from_input_file=False)
        self._inputField2 = InputFieldTemplate.objects.create(template=self._task3,
                                                              label='input2',
                                                              description="Input field 2",
                                                              amount=4,
                                                              measure=self._millilitre,
                                                              lookup_type=self._prodinput,
                                                              from_input_file=False)
        self._task3.input_fields.add(self._inputField1)
        self._task3.input_fields.add(self._inputField2)
        self._variableField = VariableFieldTemplate.objects.create(
            template=self._task3,
            label="variable1",
            description="Variable field 1",
            amount=3.3,
            measure=self._millilitre,
            measure_not_required=False)
        self._task3.variable_fields.add(self._variableField)
        self._outputField = OutputFieldTemplate.objects.create(template=self._task3,
                                                               label='output1',
                                                               description="Output field 1",
                                                               amount=9.6,
                                                               measure=self._millilitre,
                                                               lookup_type=self._prodinput)
        self._task3.output_fields.add(self._outputField)
        self._stepField = StepFieldTemplate.objects.create(template=self._task3,
                                                           label='step1',
                                                           description="Step field 1")
        self._stepFieldProperty = StepFieldProperty.objects.create(step=self._stepField,
                                                                   label='prop1',
                                                                   amount=9.6,
                                                                   measure=self._millilitre)
        self._stepField.properties.add(self._stepFieldProperty)
        self._task3.step_fields.add(self._stepField)
        self._task3.save()

        # Joe can see and edit workflow 1, and see item 2 but not edit it. No access to 3.
        # Jane can see and edit items 3+2, and see item 1 but not edit it.
        ViewPermissionsMixin().assign_permissions(instance=self._task1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._task2,
                                                  permissions={"joe_group": "r",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._task3,
                                                  permissions={"jane_group": "rw"})
        self._human = Organism.objects.create(name="Homo sapiens", common_name="Human")
        self._itemLW = Item.objects.create(name="Item_LW", item_type=self._prodinput,
                                           amount_measure=self._millilitre,
                                           amount_available=10,
                                           added_by=self._joeBloggs, identifier="iLW")
        self._item1 = Item.objects.create(name="Item_1", item_type=self._prodinput,
                                          amount_measure=self._millilitre,
                                          amount_available=10,
                                          added_by=self._joeBloggs, identifier="i1")
        self._item2 = Item.objects.create(name="Item_2", item_type=self._prodinput,
                                          amount_measure=self._millilitre,
                                          amount_available=20,
                                          added_by=self._joeBloggs, identifier="i2")
        self._item3 = Item.objects.create(name="item_3", item_type=self._prodinput,
                                          amount_measure=self._millilitre,
                                          amount_available=30,
                                          added_by=self._joeBloggs, identifier="i3")

        self._joeBloggsOrder = \
            Order.objects.create(name="Order1",
                                 status="In Limbo",
                                 data={},
                                 status_bar_status="Submitted",
                                 user=self._joeBloggs,
                                 is_quote=False,
                                 quote_sent=False,
                                 po_receieved=False,
                                 po_reference=None,
                                 invoice_sent=False,
                                 has_paid=False)
        self._joeBloggsProject = \
            Project.objects.create(name="Joe's Project",
                                   description="Awfully interesting",
                                   order=self._joeBloggsOrder,
                                   created_by=self._joeBloggs,
                                   archive=False,
                                   primary_lab_contact=self._staffUser)

        self._janeDoeOrder = \
            Order.objects.create(name="Order2",
                                 status="Also in limbo",
                                 data={},
                                 status_bar_status="Submitted",
                                 user=self._janeDoe,
                                 is_quote=False,
                                 quote_sent=False,
                                 po_receieved=False,
                                 po_reference=None,
                                 invoice_sent=False,
                                 has_paid=False)
        self._janeDoeProject = \
            Project.objects.create(name="Jane's Project",
                                   description="Even more insightful",
                                   order=self._janeDoeOrder,
                                   created_by=self._janeDoe,
                                   archive=True,
                                   primary_lab_contact=self._staffUser)

        # We have to simulate giving Joe and Jane's groups access to these projects. Joe can see and
        # edit only his.
        # Jane can see and edit hers, and see Joe's but not edit it.
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProject,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._janeDoeProject,
                                                  permissions={"jane_group": "rw"})

        # We also have to give Joe and Jane permission to view projects before they can create
        # products for those projects.
        self._joeBloggs.user_permissions.add(Permission.objects.get(codename="view_project"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_project"))

        # Now we give Joe and Jane general permissions at the product level
        self._joeBloggs.user_permissions.add(Permission.objects.get(codename="view_product"))
        self._joeBloggs.user_permissions.add(Permission.objects.get(codename="change_product"))
        self._joeBloggs.user_permissions.add(Permission.objects.get(codename="delete_product"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_product"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="change_product"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="delete_product"))

        # Now that we have projects, we can finally create the test products for them. Note no
        # design and hence no inventory items associated.
        self._joeBloggsProduct = \
            Product.objects.create(name="Product1", status=ProductStatus.objects.get(name="Added"),
                                   product_type=self._prodinput,
                                   optimised_for=self._human,
                                   created_by=self._joeBloggs,
                                   project=self._joeBloggsProject)
        self._joeBloggsProduct.linked_inventory.add(self._item1)
        self._joeBloggsProduct.linked_inventory.add(self._item2)
        self._joeBloggsProduct.save()
        self._janeDoeProduct = \
            Product.objects.create(name="Product2", status=ProductStatus.objects.get(name="Added"),
                                   product_type=self._prodinput,
                                   optimised_for=self._human,
                                   created_by=self._janeDoe,
                                   project=self._janeDoeProject)
        self._janeDoeProduct.linked_inventory.add(self._item3)
        self._janeDoeProduct.save()
        self._jimBeamProduct = \
            Product.objects.create(name="Product3", status=ProductStatus.objects.get(name="Added"),
                                   product_type=self._prodinput,
                                   optimised_for=self._human,
                                   created_by=self._janeDoe,
                                   project=self._janeDoeProject)
        self._jimBeamProduct.linked_inventory.add(self._item3)
        self._jimBeamProduct.save()

        self._run1 = \
            Run.objects.create(
                name="run1",
                tasks='%d,%d,%d' % (self._task3.id, self._task2.id, self._task1.id),
                started_by=self._joeBloggs)
        self._run1.products.add(self._joeBloggsProduct)
        self._run1.products.add(self._jimBeamProduct)
        self._runlabware = \
            RunLabware.objects.create(identifier="lw1",
                                      labware=self._item3,
                                      is_active=False)
        self._run1.labware.add(self._runlabware)
        ViewPermissionsMixin().assign_permissions(instance=self._run1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        self._run1.save()

        self._run2 = \
            Run.objects.create(
                name="run2",
                tasks='%d,%d' % (self._task4.id, self._task1.id),
                started_by=self._janeDoe)
        self._run2.labware.add(self._runlabware)
        ViewPermissionsMixin().assign_permissions(instance=self._run2,
                                                  permissions={"jane_group": "rw"})
        self._run2.save()

        # We also have to give Joe and Jane permission to view, change and delete runs in
        # general.
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="add_run"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="view_run"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="change_run"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="delete_run"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="add_run"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_run"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="change_run"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="delete_run"))

    def test_presets(self):
        self.assertEqual(Run.objects.count(), 2)
        self.assertIs(Run.objects.filter(name="run1").exists(), True)
        self.assertIs(Run.objects.filter(name="run2").exists(), True)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/runs/%d/' % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/runs/%d/' % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see items his group can see
        self._asJoeBloggs()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        runs = response.data
        self.assertEqual(len(runs["results"]), 1)
        r = runs["results"][0]
        self.assertEqual(r["name"], "run1")

    def test_user_list_group(self):
        # Jane can see all because her group permissions permit this
        self._asJaneDoe()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        runs = response.data
        self.assertEqual(len(runs["results"]), 2)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/runs/%d/' % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r = response.data
        self.assertEqual(r["name"], "run1")

    def test_user_view_other(self):
        # Jane's run 2 is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/runs/%d/' % self._run2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's items 1+2
        self._asJaneDoe()
        response = self._client.get('/runs/%d/' % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r = response.data
        self.assertEqual(r["name"], "run1")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        runs = response.data
        self.assertEqual(len(runs["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/runs/%d/' % self._run2.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        r = response.data
        self.assertEqual(r["name"], "run2")

    def test_user_create(self):
        self._asJaneDoe()
        new_run = {"name": "run3",
                   "tasks": '%d,%d,%d' % (self._task1.id, self._task2.id, self._task3.id),
                   "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/runs/", new_run, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Run.objects.count(), 3)
        self.assertEqual(Run.objects.filter(name="run3").count(), 1)
        r = Run.objects.filter(name="run3").all()[0]
        self.assertEqual(r.started_by, self._janeDoe)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        runs = response.data
        self.assertEqual(len(runs["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        runs = response.data
        self.assertEqual(len(runs["results"]), 3)

    def test_admin_create(self):
        # Admin should be able to create a set for someone else
        self._asAdmin()
        new_run = {"name": "run3",
                   "tasks": '%d,%d,%d' % (self._task1.id, self._task2.id, self._task3.id),
                   "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/runs/", new_run, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Run.objects.count(), 3)
        self.assertEqual(Run.objects.filter(name="run3").count(), 1)
        r = Run.objects.filter(name="run3").all()[0]
        self.assertEqual(r.started_by, self._adminUser)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        runs = response.data
        self.assertEqual(len(runs["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/runs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        runs = response.data
        self.assertEqual(len(runs["results"]), 3)

    def test_user_edit_own(self):
        self._asJoeBloggs()
        update_run = {"name": "runX"}
        response = self._client.patch("/runs/%d/" % self._run1.id,
                                      update_run, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Run.objects.filter(name="run1").exists(), False)
        self.assertIs(Run.objects.filter(name="runX").exists(), True)

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's item 2
        self._asJoeBloggs()
        update_run = {"name": "runX"}
        response = self._client.patch("/runs/%d/" % self._run2.id,
                                      update_run, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_edit_other_readonly(self):
        # Jane can see but not edit Joe's item 1
        self._asJaneDoe()
        update_run = {"name": "runX"}
        response = self._client.patch("/runs/%d/" % self._run1.id,
                                      update_run, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's item 1 first so she can edit it
        ViewPermissionsMixin().assign_permissions(instance=self._run1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        update_run = {"name": "runX"}
        response = self._client.patch("/runs/%d/" % self._run1.id,
                                      update_run, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Run.objects.filter(name="run1").exists(), False)
        self.assertIs(Run.objects.filter(name="runX").exists(), True)

    def test_admin_edit_any(self):
        self._asAdmin()
        update_run = {"name": "runX"}
        response = self._client.patch("/runs/%d/" % self._run1.id,
                                      update_run, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Run.objects.filter(name="run1").exists(), False)
        self.assertIs(Run.objects.filter(name="runX").exists(), True)

    def test_user_delete_own(self):
        self._asJoeBloggs()
        response = self._client.delete("/runs/%d/" % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Run.objects.filter(name="run1").exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/runs/%d/" % self._run2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Run.objects.filter(name="run2").exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/runs/%d/" % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Run.objects.filter(name="run1").exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._run1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/runs/%d/" % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Run.objects.filter(name="run1").exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/runs/%d/" % self._run1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Run.objects.filter(name="run1").exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own sets
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch(
            "/runs/%d/set_permissions/" % self._run1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        permissions = {"jane_group": "r"}
        response = self._client.patch(
            "/runs/%d/set_permissions/" % self._run2.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        w = Run.objects.get(name="run2")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch(
            "/runs/%d/set_permissions/" % self._run1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._run1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/runs/%d/set_permissions/" % self._run1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_admin_set_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/runs/%d/set_permissions/" % self._run1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_set_permissions_invalid_group(self):
        # An invalid group should throw a 400 data error
        self._asAdmin()
        permissions = {"jim_group": "r"}
        response = self._client.patch(
            "/runs/%d/set_permissions/" % self._run1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch(
            "/runs/%d/set_permissions/" % self._run1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the permission wasn't changed accidentally in the process
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/runs/%d/remove_permissions/?groups=joe_group" % self._run1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's item 4
        self._asJoeBloggs()
        response = self._client.delete(
            "/runs/%d/remove_permissions/?groups=jane_group" % self._run2.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        w = Run.objects.get(name="run2")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's item 1
        self._asJaneDoe()
        response = self._client.delete(
            "/runs/%d/remove_permissions/?groups=joe_group" % self._run1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._run1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/runs/%d/remove_permissions/?groups=joe_group" % self._run1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/runs/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._run1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = Run.objects.get(name="run1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), None)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_remove_permissions_invalid_group(self):
        # An invalid group name should fail quietly - we don't care if permissions can't be
        # removed as the end result is the same, i.e. that group can't access anything
        self._asAdmin()
        response = self._client.delete(
            "/runs/%d/remove_permissions/?groups=jim_group" %
            self._run1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_workflow_from_run_noname(self):
        self._asAdmin()
        response = self._client.post(
            "/runs/%d/workflow_from_run/" %
            self._run1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Please supply a name")

    def test_workflow_from_run(self):
        self._asAdmin()
        response = self._client.post(
            "/runs/%d/workflow_from_run/?name=w99" %
            self._run1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER)
        self.assertEqual(Workflow.objects.count(), 1)
        w = Workflow.objects.all()[0]
        self.assertIs(response.get("location").endswith("/workflows/%d/" % w.id), True)

    def _setup_test_task_recalculation(self):
        return {
            "id": self._task1.id,
            "product_input_measure": self._millilitre.symbol,
            "product_input_amount": 5,
            "product_input": self._prodinput.name,
            "input_files": [self._inputTempl.name],
            "output_files": [self._outputTempl.name],
            "equipment_files": [self._equipTempl1.name],
            "labware": self._labware.name,
            "store_labware_as": "labware_identifier",
            "capable_equipment": [self._equipmentSequencer.name],
            "name": "NewTask",
            "assign_groups": {"jane_group": "rw"},
            "input_fields": [
                {"measure": self._millilitre.symbol,
                 "lookup_type": self._prodinput.name,
                 "label": "input1",
                 "amount": 6.2,
                 "template": self._task3.id,
                 "calculation_used": self._calcField.id,
                 "from_calculation": False},
                {"measure": self._millilitre.symbol,
                 "lookup_type": self._prodinput.name,
                 "label": "input2",
                 "amount": 4.3,
                 "template": self._task3.id,
                 "calculation_used": self._calcField.id,
                 "from_calculation": False}],
            "step_fields": [
                {"label": "step1",
                 "template": self._task3.id,
                 "properties": [{"id": self._stepFieldProperty.id,
                                 "measure": self._millilitre.symbol,
                                 "label": "prop1",
                                 "amount": 9.9,
                                 "calculation_used": self._calcField.id,
                                 "from_calculation": False}]}],
            "variable_fields": [
                {"measure": self._millilitre.symbol,
                 "label": "variable1",
                 "amount": 8.4,
                 "template": self._task3.id}],
            "output_fields": [
                {"measure": self._millilitre.symbol,
                 "lookup_type": self._prodinput.name,
                 "label": "output1",
                 "amount": 9.6,
                 "template": self._task3.id,
                 "calculation_used": self._calcField.id,
                 "from_calculation": False}],
            "calculation_fields": [
                {"id": self._calcField.id,
                 "label": "calc1",
                 "calculation": ("{input1}"
                                 "+{input2}"
                                 "/{variable1}"
                                 "*{prop1}"
                                 "+{product_input_amount}"),
                 "template": self._task3.id}],
            "created_by": self._janeDoe.username}

    def test_user_recalculate_nonread_task(self):
        updated_task = self._setup_test_task_recalculation()
        self._asJoeBloggs()
        response = self._client.post("/runs/%d/recalculate/" % self._run2.id,
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_recalculate_readonly_task(self):
        updated_task = self._setup_test_task_recalculation()
        self._asJaneDoe()
        response = self._client.post("/runs/%d/recalculate/" % self._run1.id,
                                     # ID mismatch doesn't matter as won't get that far 
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_recalculate_readwrite_task(self):
        updated_task = self._setup_test_task_recalculation()
        self._asJoeBloggs()
        response = self._client.post("/runs/%d/recalculate/" % self._run1.id,
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["calculation_fields"][0]["result"], 16.267857142857142)

    def test_admin_recalculate_task(self):
        updated_task = self._setup_test_task_recalculation()
        self._asAdmin()
        response = self._client.post("/runs/%d/recalculate/" % self._run1.id,
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["calculation_fields"][0]["result"], 16.267857142857142)

    def _prepare_start_task(self, product_input_amount=1.0):
        # TODO add some input_files once file handling in Run is working properly
        return {"task": json.dumps({
            "id": self._task3.id,
            "labware_amount": 1.0,
            "multiple_products_on_labware": False,
            "product_input": self._prodinput.name,
            "product_input_amount": product_input_amount,
            "product_input_measure": self._millilitre.symbol,
            "equipment_choice": self._equipmentSequencer.name,
            "input_fields": [
                {"id:": self._inputField1.id, "measure": self._millilitre.symbol,
                 "lookup_type": self._prodinput.name, "label": "input1",
                 "amount": 2.0, "template": self._task3.id,
                 "inventory_identifier": "i1", "from_input_file": False},
                {"id:": self._inputField2.id, "measure": self._millilitre.symbol,
                 "lookup_type": self._prodinput.name, "label": "input2",
                 "amount": 3.0, "template": self._task3.id,
                 "inventory_identifier": "i2", "from_input_file": False}],
            'output_fields': [
                {"id": self._outputField.id, "measure": self._millilitre.symbol,
                 "lookup_type": self._prodinput.name, "label": "output1",
                 "amount": 5.0, "template": self._task3.id}],
            'labware_identifier': self._itemLW.identifier,
            'calculation_fields': [],
            'step_fields': [],
            'variable_fields': [],
        }),
            "input_files": []  # array of {filetemplate.name,filehandle}
        }

    def test_start_task_check(self):
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/?is_check=True" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # if preview then return [] of ItemTransferPreviewSerializer
        r = response.data["requirements"]
        self.assertEqual(len(r), 4)
        ir = {x["item"]["identifier"]: x["amount_taken"] for x in r}
        self.assertEqual(ir["i1"], 5)
        self.assertEqual(ir["i2"], 7)
        self.assertEqual(ir["i3"], 1)
        self.assertEqual(ir["iLW"], 1)
        # check update WorkflowProduct uuid and active fields for each Product on ActiveWorkflow
        run = Run.objects.get(id=self._run1.id)
        self.assertEqual(run.task_run_identifier, None)
        self.assertIs(run.task_in_progress, False)
        self.assertIs(run.has_started, False)
        # check create ItemTransfers per input item
        self.assertEqual(ItemTransfer.objects.count(), 0)
        # check one DataEntry per input product item
        self.assertEqual(DataEntry.objects.count(), 0)
        # check update inventory amounts
        self.assertEqual(Item.objects.get(id=self._item1.id).amount_available, 10)
        self.assertEqual(Item.objects.get(id=self._item2.id).amount_available, 20)
        self.assertEqual(Item.objects.get(id=self._item3.id).amount_available, 30)
        self.assertEqual(Item.objects.get(id=self._itemLW.id).amount_available, 10)

    def test_start_task_insufficient_inventory(self):
        start_task = self._prepare_start_task(product_input_amount=99)
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # if not enough amounts then 400 and message:
        #   Inventory item {} ({}) is short of amount by {}'.format(
        #                item.identifier, item.name, missing \n next etc.
        self.assertNotEqual(response.data["message"].find(
            "Inventory item i1 (Item_1) is short of amount by 93.00 milliliter"), -1)
        self.assertNotEqual(response.data["message"].find(
            "Inventory item i2 (Item_2) is short of amount by 85.00 milliliter"), -1)
        self.assertNotEqual(response.data["message"].find(
            "Inventory item i3 (item_3) is short of amount by 69.00 milliliter"), -1)
        # check update WorkflowProduct uuid and active fields for each Product on ActiveWorkflow
        run = Run.objects.get(id=self._run1.id)
        self.assertEqual(run.task_run_identifier, None)
        self.assertIs(run.task_in_progress, False)
        self.assertIs(run.has_started, False)
        # check create ItemTransfers per input item
        self.assertEqual(ItemTransfer.objects.count(), 0)
        # check one DataEntry per input product item
        self.assertEqual(DataEntry.objects.count(), 0)
        # check update inventory amounts
        self.assertEqual(Item.objects.get(id=self._item1.id).amount_available, 10)
        self.assertEqual(Item.objects.get(id=self._item2.id).amount_available, 20)
        self.assertEqual(Item.objects.get(id=self._item3.id).amount_available, 30)
        self.assertEqual(Item.objects.get(id=self._itemLW.id).amount_available, 10)

    def test_start_task(self):
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started successfully")
        # check update WorkflowProduct uuid and active fields for each Product on ActiveWorkflow
        run = Run.objects.get(id=self._run1.id)
        self.assertIs(run.task_in_progress, True)
        self.assertIs(run.has_started, True)
        uuid = run.task_run_identifier
        # check create ItemTransfers per input item
        its = ItemTransfer.objects.filter(run_identifier=uuid)
        self.assertEqual(its.count(), 4)
        for it in its.all():
            self.assertIs(it.transfer_complete, True)
        # check one DataEntry per input product item
        self.assertEqual(DataEntry.objects.filter(task_run_identifier=uuid).count(), 2)
        # check update inventory amounts
        self.assertEqual(Item.objects.get(id=self._item1.id).amount_available, 5)
        self.assertEqual(Item.objects.get(id=self._item2.id).amount_available, 13)
        self.assertEqual(Item.objects.get(id=self._item3.id).amount_available, 29)
        self.assertEqual(Item.objects.get(id=self._itemLW.id).amount_available, 9)

    def test_monitor_task_inactive(self):
        # Get status and check data response (without starting task first)
        self._asJoeBloggs()
        response = self._client.get("/runs/%d/monitor_task/" % self._run1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_monitor_task(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started successfully")
        # Get status and check data response
        response = self._client.get("/runs/%d/monitor_task/" % self._run1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        er = {x["name"]: x["id"] for x in response.data["equipment_files"]}
        self.assertEqual(er["EquipTemplate1"], self._equipTempl1.id)
        self.assertEqual(er["EquipTemplate2"], self._equipTempl2.id)
        self.assertEqual(er["EquipTemplate3"], self._equipTempl3.id)
        self.assertEqual(response.data["transfers"],
                         ItemTransferPreviewSerializer(ItemTransfer.objects.all(), many=True).data)
        self.assertEqual(response.data["data"],
                         DataEntrySerializer(DataEntry.objects.all(), many=True).data)

    def test_get_file_inactive(self):
        # Get status and check data response (without starting task first)
        self._asJoeBloggs()
        response = self._client.get(
            "/runs/%d/get_file/?id=%d" % (self._run1.id, self._equipTempl1.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_file_invalid(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started successfully")
        # Get status and check data response (without starting task first)
        response = self._client.get(
            "/runs/%d/get_file/?id=%d" % (self._run1.id, 999), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Template does not exist")

    def test_get_file_use_inputs(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started successfully")
        # Get status and check data response (without starting task first)
        response = self._client.get(
            "/runs/%d/get_file/?id=%d" % (self._run1.id, self._equipTempl1.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        data = {(x["product_name"], x["task_input.name"]): x for x in response.data}
        self.assertEqual(data[("P101-2 Product3", "Item_1")],
                         {"labware_amount": 1,
                          "input2.measure": "ml",
                          "input2.inventory_identifier": "i2",
                          "input2.amount": 3.0,
                          "product_name": "P101-2 Product3",
                          "equipment_choice": "Sequencer",
                          "input1.measure": "ml",
                          "input1.inventory_identifier": "i1",
                          "input1.amount": 2.0,
                          "created_by": "Joe Bloggs",
                          "labware_identifier": "iLW",
                          "output1.lookup_type": "ExampleStuff",
                          "output1.amount": 5.0,
                          "task": "TaskTempl3",
                          "run": "run1",
                          "task_input.measure": "ml",
                          "task_input.name": "Item_1",
                          "task_input.amount": 2.0})
        self.assertEqual(data[("P101-2 Product3", "Item_2")],
                         {"labware_amount": 1,
                          "input2.measure": "ml",
                          "input2.inventory_identifier": "i2",
                          "input2.amount": 3.0,
                          "product_name": "P101-2 Product3",
                          "equipment_choice": "Sequencer",
                          "input1.measure": "ml",
                          "input1.inventory_identifier": "i1",
                          "input1.amount": 2.0,
                          "created_by": "Joe Bloggs",
                          "labware_identifier": "iLW",
                          "output1.lookup_type": "ExampleStuff",
                          "output1.amount": 5.0,
                          "task": "TaskTempl3",
                          "run": "run1",
                          "task_input.measure": "ml",
                          "task_input.name": "Item_2",
                          "task_input.amount": 3.0})
        self.assertEqual(data[("P101-2 Product3", "item_3")],
                         {"labware_amount": 1,
                          "input2.measure": "ml",
                          "input2.inventory_identifier": "i2",
                          "input2.amount": 3.0,
                          "product_name": "P101-2 Product3",
                          "equipment_choice": "Sequencer",
                          "input1.measure": "ml",
                          "input1.inventory_identifier": "i1",
                          "input1.amount": 2.0,
                          "created_by": "Joe Bloggs",
                          "labware_identifier": "iLW",
                          "output1.lookup_type": "ExampleStuff",
                          "output1.amount": 5.0,
                          "task": "TaskTempl3",
                          "run": "run1",
                          "task_input.measure": "ml",
                          "task_input.name": "item_3",
                          "task_input.amount": 1.0})
        self.assertEqual(data[("P100-1 Product1", "Item_1")],
                         {"labware_amount": 1,
                          "input2.measure": "ml",
                          "input2.inventory_identifier": "i2",
                          "input2.amount": 3.0,
                          "product_name": "P100-1 Product1",
                          "equipment_choice": "Sequencer",
                          "input1.measure": "ml",
                          "input1.inventory_identifier": "i1",
                          "input1.amount": 2.0,
                          "created_by": "Joe Bloggs",
                          "labware_identifier": "iLW",
                          "output1.lookup_type": "ExampleStuff",
                          "output1.amount": 5.0,
                          "task": "TaskTempl3",
                          "run": "run1",
                          "task_input.measure": "ml",
                          "task_input.name": "Item_1",
                          "task_input.amount": 1.0})
        self.assertEqual(data[("P100-1 Product1", "Item_2")],
                         {"labware_amount": 1,
                          "input2.measure": "ml",
                          "input2.inventory_identifier": "i2",
                          "input2.amount": 3.0,
                          "product_name": "P100-1 Product1",
                          "equipment_choice": "Sequencer",
                          "input1.measure": "ml",
                          "input1.inventory_identifier": "i1",
                          "input1.amount": 2.0,
                          "created_by": "Joe Bloggs",
                          "labware_identifier": "iLW",
                          "output1.lookup_type": "ExampleStuff",
                          "output1.amount": 5.0,
                          "task": "TaskTempl3",
                          "run": "run1",
                          "task_input.measure": "ml",
                          "task_input.name": "Item_2",
                          "task_input.amount": 1.0})

    def test_get_file_total_inputs(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started successfully")
        # Get status and check data response (without starting task first)
        response = self._client.get(
            "/runs/%d/get_file/?id=%d" % (self._run1.id, self._equipTempl2.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TODO Need to fix TaskTemplate.data_to_output_file then implement an appropriate test here
        self.assertIs(True, False)

    def test_get_file_default(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started successfully")
        # Get status and check data response (without starting task first)
        response = self._client.get(
            "/runs/%d/get_file/?id=%d" % (self._run1.id, self._equipTempl3.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        data = {x["product_name"]: x for x in response.data}
        self.assertEqual(data["P101-2 Product3"], {"labware_amount": 1,
                                                   "input2.measure": "ml",
                                                   "input2.inventory_identifier": "i2",
                                                   "input2.amount": 3.0,
                                                   "product_name": "P101-2 Product3",
                                                   "equipment_choice": "Sequencer",
                                                   "input1.measure": "ml",
                                                   "input1.inventory_identifier": "i1",
                                                   "input1.amount": 2.0,
                                                   "created_by": "Joe Bloggs",
                                                   "labware_identifier": "iLW",
                                                   "output1.lookup_type": "ExampleStuff",
                                                   "output1.amount": 5.0,
                                                   "task": "TaskTempl3",
                                                   "run": "run1"})
        self.assertEqual(data["P100-1 Product1"], {"labware_amount": 1,
                                                   "input2.measure": "ml",
                                                   "input2.inventory_identifier": "i2",
                                                   "input2.amount": 3.0,
                                                   "product_name": "P100-1 Product1",
                                                   "equipment_choice": "Sequencer",
                                                   "input1.measure": "ml",
                                                   "input1.inventory_identifier": "i1",
                                                   "input1.amount": 2.0,
                                                   "created_by": "Joe Bloggs",
                                                   "labware_identifier": "iLW",
                                                   "output1.lookup_type": "ExampleStuff",
                                                   "output1.amount": 5.0,
                                                   "task": "TaskTempl3",
                                                   "run": "run1"})

    def test_finish_task_inactive(self):
        # Get status and check data response (without starting task first)
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/finish_task/" % self._run1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_finish_task(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/runs/%d/start_task/" % self._run1.id, data=start_task)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started successfully")
        # Create temp file to copy from equipment
        run = Run.objects.get(id=self._run1.id)
        rtri = run.task_run_identifier
        real_from_path = os.path.join(self._copyFile.copy_from_prefix,
                                      "%s%sA" % (self._tempfilePrefix, str(rtri)))
        real_to_path = os.path.join(self._copyFile.copy_from_prefix,
                                    "%s%sB" % (self._tempfilePrefix, str(rtri)))
        file = open(real_from_path, 'w')
        file.write("Lots of interesting stuff")
        file.close()
        # Finish task and mark one product as a failure (the other is a success)
        response = self._client.post(
            "/runs/%d/finish_task/" % self._run1.id,
            {"failures": self._joeBloggsProduct.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check new Run because of failure
        run = Run.objects.get(id=self._run1.id)  # Yes, really, must reload here
        new_name = '{} (failed)'.format(run.name)
        self.assertIs(Run.objects.filter(name=new_name).exists(), True)
        new_run = Run.objects.get(name=new_name)
        self.assertEqual(new_run.tasks, run.tasks)
        self.assertEqual(new_run.current_task, 0)
        self.assertIs(new_run.has_started, True)
        self.assertEqual(new_run.started_by, self._joeBloggs)
        self.assertEqual(new_run.products.count(), 1)
        self.assertEqual(new_run.products.all()[0], self._joeBloggsProduct)
        # Check DataEntry failed items
        failed_entries = DataEntry.objects.filter(task_run_identifier=rtri, state="failed")
        self.assertEqual(failed_entries.count(), 1)
        self.assertEqual(failed_entries.all()[0].product, self._joeBloggsProduct)
        self.assertEqual(new_run.products.count(), 1)
        self.assertEqual(new_run.products.all()[0], self._joeBloggsProduct)
        # Check DataEntry succeeded
        success_entries = DataEntry.objects.filter(task_run_identifier=run.task_run_identifier,
                                                   state="succeeded")
        self.assertEqual(success_entries.count(), 1)
        self.assertEqual(success_entries.all()[0].product, self._jimBeamProduct)
        self.assertEqual(run.products.count(), 1)
        self.assertEqual(run.products.all()[0], self._jimBeamProduct)
        self.assertIs(run.labware.filter(is_active=True).exists(), False)
        # Check new Items from OutputFields
        e = success_entries[0]
        output_name = '{} {}/{}'.format(e.product.product_identifier,
                                        e.product.name,
                                        "output1")
        self.assertIs(Item.objects.filter(name=output_name).exists(), True)
        output = Item.objects.get(name=output_name)
        self.assertEqual(output.amount_measure, self._millilitre)
        self.assertEqual(output.identifier, '{}/{}/0'.format(rtri, 0, 0))
        self.assertEqual(output.item_type, self._prodinput)
        self.assertEqual(output.location, Location.objects.get(name="Lab"))
        self.assertEqual(output.amount_available, 5.0)
        self.assertEqual(output.added_by, self._joeBloggs)
        self.assertEqual(output.created_from.count(), 1)
        self.assertEqual(output.created_from.all()[0], self._item3)
        self.assertIn(output, e.product.linked_inventory.all())
        # Check filepath copy from equipment
        self.assertEqual(e.data_files.count(), 1)
        df = e.data_files.all()[0]
        self.assertEqual(df.file_name, os.path.basename(real_to_path))
        self.assertEqual(df.location, real_to_path)
        self.assertEqual(df.equipment, self._equipmentSequencer)
        self.assertIs(filecmp.cmp(os.path.join(real_from_path), os.path.join(real_to_path)), True)
        # Clean up
        os.remove(real_from_path)
        os.remove(real_to_path)
        # Check task in progress false
        self.assertIs(run.task_in_progress, False)
        # Check current task increment
        self.assertEqual(run.current_task, 1)
        # Check response = Run.serializer
        runresp = response.data
        self.assertEqual(runresp["name"], "run1")
        self.assertIs(runresp["task_in_progress"], False)
        self.assertEqual(len(runresp["transfers"]), 4)
        self.assertEqual(runresp["started_by"], "Joe Bloggs")
        self.assertIs(runresp["is_active"], True)
        self.assertIs(runresp["has_started"], True)
        self.assertEqual(runresp["id"], self._run1.id)
        self.assertEqual(len(runresp["labware"]), 1)
        self.assertEqual(runresp["labware"][0], self._runlabware.id)
        self.assertEqual(len(runresp["products"]), 1)
        self.assertEqual(runresp["products"][0], self._jimBeamProduct.id)
        self.assertEqual(runresp["tasks"],
                         "%d,%d,%d" % (self._task3.id, self._task2.id, self._task1.id))
