from django.contrib.auth.models import Permission, Group
from rest_framework import status
from lims.shared.loggedintestcase import LoggedInTestCase
from .models import Workflow, WorkflowProduct, ActiveWorkflow, TaskTemplate, \
    CalculationFieldTemplate, InputFieldTemplate, \
    VariableFieldTemplate, OutputFieldTemplate, StepFieldTemplate, StepFieldProperty, DataEntry
from lims.filetemplate.models import FileTemplate, FileTemplateField
from lims.inventory.models import Location, Item, ItemType, AmountMeasure, ItemTransfer
from lims.equipment.models import Equipment
from .views import ViewPermissionsMixin
from lims.projects.models import Project, Order, Product, ProductStatus
from lims.shared.models import Organism


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
        self.assertEqual(w.created_by, self._janeDoe)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 3)
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
                    "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/tasks/", new_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(TaskTemplate.objects.count(), 4)
        self.assertIs(TaskTemplate.objects.filter(name="NewTask").exists(), True)
        t = TaskTemplate.objects.get(name="NewTask")
        self.assertEqual(t.description, "Description")
        self.assertEqual(t.created_by, self._janeDoe)
        self.assertEqual(t.capable_equipment.all(), [self._equipmentSequencer])
        self.assertEqual(t.input_files.all(), [self._inputTempl])
        self.assertEqual(t.output_files.all(), [self._outputTempl])

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
        self._calcField = CalculationFieldTemplate.objects.create(template=self._task1,
                                                                  label='calc1',
                                                                  description="Calculation field 1",
                                                                  calculation="{input1}+{input2}*{output1]}/{variable1}*{prop1}+{product_input_amount}")
        self._task3.calculation_fields.add(self._calcField)
        self._inputField1 = InputFieldTemplate.objects.create(template=self._task1,
                                                              label='input1',
                                                              description="Input field 1",
                                                              amount=1.0,
                                                              measure=self._millilitre,
                                                              lookup_type=self._prodinput,
                                                              from_input_file=False)
        self._inputField2 = InputFieldTemplate.objects.create(template=self._task1,
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
        self._outputField = OutputFieldTemplate.objects.create(template=self._task1,
                                                               label='output1',
                                                               description="Output field 1",
                                                               amount=9.6,
                                                               measure=self._millilitre,
                                                               lookup_type=self._prodinput)
        self._task3.output_fields.add(self._outputField)
        self._stepField = StepFieldTemplate.objects.create(template=self._task1,
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
                "labware": self._labware.name,
                "store_labware_as": "labware_identifier",
                "capable_equipment": [self._equipmentSequencer.name],
                "name": "NewTask",
                "assign_groups": {"jane_group": "rw"},
                "input_fields": [{"measure": self._millilitre.symbol,
                                  "lookup_type": self._prodinput.name, "label": "input1",
                                  "amount": 6.2, "template": self._task3.id},
                                 {"measure": self._millilitre.symbol,
                                  "lookup_type": self._prodinput.name, "label": "input2",
                                  "amount": 4.3, "template": self._task3.id}],
                "step_fields": [
                    {"label": "step1", "template": self._task3.id,
                     "properties": [{"id": self._stepFieldProperty.id,
                                     "measure": self._millilitre.symbol,
                                     "label": "prop1", "amount": 9.9}]}],
                "variable_fields": [
                    {"measure": self._millilitre.symbol, "label": "variable1",
                     "amount": 8.4, "template": self._task3.id}],
                "output_fields": [{"measure": self._millilitre.symbol,
                                   "lookup_type": self._prodinput.name, "label": "output1",
                                   "amount": 9.6, "template": self._task3.id}],
                "calculation_fields": [{"id": self._calcField.id,
                                        "label": "calc1",
                                        "calculation": ("{input1}"
                                                        "+{input2}"
                                                        "*{output1]}"
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
        self.assertEqual(response.data["calculation_fields"][0]["result"],
                         6.2 + 4.3 * 9.6 / 8.4 * 9.9 + 5.2)

    def test_admin_recalculate_task(self):
        self._setup_test_task_fields()
        updated_task = self._setup_test_task_recalculation()
        self._asAdmin()
        response = self._client.post("/tasks/%d/recalculate/" % self._task3.id,
                                     updated_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["calculation_fields"][0]["result"],
                         6.2 + 4.3 * 9.6 / 8.4 * 9.9 + 5)

    def test_user_listall_taskfield_readonly(self):
        self._setup_test_task_fields()
        # Make Jane temporarily readonly on her task
        ViewPermissionsMixin().assign_permissions(instance=self._task3,
                                                  permissions={"jane_group": "r"})
        self._asJaneDoe()
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._stepField.label)

    def test_user_listall_taskfield_nonread(self):
        self._setup_test_task_fields()
        self._asJoeBloggs()
        # Joe should see none as all on Jane's
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(len(t), 0)

    def test_user_listall_taskfield_readwrite(self):
        self._setup_test_task_fields()
        self._asJaneDoe()
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._stepField.label)

    def test_admin_listall_taskfield_any(self):
        self._setup_test_task_fields()
        self._asAdmin()
        response = self._client.get('/taskfields/?type=%s' % "Step")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._stepField.label)
        response = self._client.get('/taskfields/?type=%s' % "Input")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(len(t), 2)
        self.assertEqual(t[0]["label"], self._inputField1.label)
        self.assertEqual(t[1]["label"], self._inputField2.label)
        response = self._client.get('/taskfields/?type=%s' % "Output")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._outputField.label)
        response = self._client.get('/taskfields/?type=%s' % "Variable")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0]["label"], self._variableField.label)
        response = self._client.get('/taskfields/?type=%s' % "Calculation")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t = response.data
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
        self.assertEqual(len(self._task3.step_fields), 1)
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
        self.assertEqual(len(self._task3.step_fields), 1)
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
        self.assertEqual(len(self._task3.step_fields), 2)
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
        updated_taskfield = {"description": "Blah"}
        response = self._client.patch('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"),
                                      updated_taskfield)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
        response = self._client.delete('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), False)

    def test_admin_delete_taskfield_any(self):
        self._setup_test_task_fields()
        self._asAdmin()
        response = self._client.delete('/taskfields/%d/?type=%s' % (self._stepField.id, "Step"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(self._task3.step_fields.filter(description="Step field 1").exists(), False)


class ActiveWorkflowTestCase(LoggedInTestCase):
    def setUp(self):
        super(ActiveWorkflowTestCase, self).setUp()

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

        self._prodinput = ItemType.objects.create(name="ExampleStuff", parent=None)
        self._labware = ItemType.objects.create(name="ExampleLabware", parent=None)
        self._millilitre = AmountMeasure.objects.create(name="Millilitre", symbol="ml")
        self._location = Location.objects.create(name="Lab", code="L1")
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

        self._calcField = CalculationFieldTemplate.objects.create(template=self._task1,
                                                                  label='calc1',
                                                                  description="Calculation field 1",
                                                                  calculation="{input1}+{input2}*{output1]}/{variable1}*{prop1}+{product_input_amount}")
        self._task3.calculation_fields.add(self._calcField)
        self._inputField1 = InputFieldTemplate.objects.create(template=self._task1,
                                                              label='input1',
                                                              description="Input field 1",
                                                              amount=1,
                                                              measure=self._millilitre,
                                                              lookup_type=self._prodinput,
                                                              from_input_file=False)
        self._inputField2 = InputFieldTemplate.objects.create(template=self._task1,
                                                              label='input2',
                                                              description="Input field 2",
                                                              amount=4,
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
        self._outputField = OutputFieldTemplate.objects.create(template=self._task1,
                                                               label='output1',
                                                               description="Output field 1",
                                                               amount=9.6,
                                                               measure=self._millilitre,
                                                               lookup_type=self._prodinput)
        self._task3.output_fields.add(self._outputField)
        self._stepField = StepFieldTemplate.objects.create(template=self._task1,
                                                           label='step1',
                                                           description="Step field 1")
        self._stepFieldProperty = StepFieldProperty.objects.create(step=self._stepField,
                                                                   label='prop1',
                                                                   amount=9.6,
                                                                   measure=self._millilitre)
        self._stepField.properties.add(self._stepFieldProperty)
        self._task3.step_fields.add(self._stepField)
        self._task3.save()

        self._workflow1 = Workflow.objects.create(name="Workflow1",
                                                  order='%d,%d' % (self._task1.id, self._task2.id),
                                                  created_by=self._joeBloggs)
        self._workflow2 = Workflow.objects.create(name="Workflow2", order='%d,%d,%d' % (
            self._task1.id, self._task3.id, self._task4.id), created_by=self._janeDoe)
        self._workflow3 = Workflow.objects.create(name="Workflow3", order='%d,%d,%d' % (
            self._task3.id, self._task2.id, self._task1.id), created_by=self._janeDoe)

        self._activeWorkflow1 = ActiveWorkflow.objects.create(workflow=self._workflow1,
                                                              started_by=self._joeBloggs)
        self._activeWorkflow2 = ActiveWorkflow.objects.create(workflow=self._workflow2,
                                                              started_by=self._janeDoe)
        self._activeWorkflow3 = ActiveWorkflow.objects.create(workflow=self._workflow3,
                                                              started_by=self._janeDoe)

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
        ViewPermissionsMixin().assign_permissions(instance=self._activeWorkflow1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._activeWorkflow2,
                                                  permissions={"joe_group": "r",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._activeWorkflow3,
                                                  permissions={"jane_group": "rw"})

        # We also have to give Joe and Jane permission to view, change and delete items in
        # general.
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="add_activeworkflow"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="view_activeworkflow"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="change_activeworkflow"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="delete_activeworkflow"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="add_activeworkflow"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_activeworkflow"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="change_activeworkflow"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="delete_activeworkflow"))

        self._human = Organism.objects.create(name="Homo sapiens", common_name="Human")
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

        # Add to one active workflow
        self._workflowProductJoe = WorkflowProduct.objects.create(product=self._joeBloggsProduct)
        self._activeWorkflow1.product_statuses.add(self._workflowProductJoe)
        self._workflowProductJim = WorkflowProduct.objects.create(product=self._jimBeamProduct)
        self._activeWorkflow1.product_statuses.add(self._workflowProductJim)
        self._activeWorkflow1.save()

    def test_presets(self):
        self.assertEqual(ActiveWorkflow.objects.count(), 3)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow1).exists(), True)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow2).exists(), True)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow3).exists(), True)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/activeworkflows/%d/' % self._activeWorkflow1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/activeworkflows/%d/' % self._activeWorkflow1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see items his group can see
        self._asJoeBloggs()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        w = wflows["results"][0]
        self.assertEqual(w["workflow"], self._workflow2.id)

    def test_user_list_group(self):
        # Jane can see all four because her group permissions permit this
        self._asJaneDoe()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 3)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/activeworkflows/%d/' % self._activeWorkflow1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = response.data
        self.assertEqual(w["workflow"], self._workflow1.id)

    def test_user_view_other(self):
        # Jane's item 4 is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/activeworkflows/%d/' % self._activeWorkflow3.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's items 1+2
        self._asJaneDoe()
        response = self._client.get('/activeworkflows/%d/' % self._activeWorkflow1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = response.data
        self.assertEqual(w["workflow"], self._workflow1.id)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 3)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/activeworkflows/%d/' % self._activeWorkflow2.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = response.data
        self.assertEqual(w["workflow"], self._activeWorkflow2.id)

    def test_user_create_own(self):
        self._asJaneDoe()
        new_wflow = {"workflow": self._workflow3.id,
                     "started_by": self._janeDoe.id,
                     "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/activeworkflows/", new_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(ActiveWorkflow.objects.count(), 4)
        self.assertEqual(ActiveWorkflow.objects.filter(workflow=self._workflow3).count(), 2)
        w = ActiveWorkflow.objects.filter(workflow=self._workflow3).all()[1]
        self.assertEqual(w.started_by, self._janeDoe)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        self._asJaneDoe()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 4)

    def test_user_create_other_readonly(self):
        self._asJoeBloggs()
        new_wflow = {"workflow": self._workflow3.id,
                     "started_by": self._joeBloggs.id,
                     "assign_groups": {"joe_group": "rw"}}
        response = self._client.post("/activeworkflows/", new_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_create_other_readonly(self):
        self._asJoeBloggs()
        new_wflow = {"workflow": self._workflow2.id,
                     "started_by": self._joeBloggs.id,
                     "assign_groups": {"joe_group": "rw"}}
        response = self._client.post("/activeworkflows/", new_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(ActiveWorkflow.objects.count(), 4)
        self.assertEqual(ActiveWorkflow.objects.filter(workflow=self._workflow2).count(), 2)
        w = ActiveWorkflow.objects.filter(workflow=self._workflow2).all()[1]
        self.assertEqual(w.started_by, self._joeBloggs)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 3)
        self._asJaneDoe()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 3)

    def test_admin_create_any(self):
        # Admin should be able to create a set for someone else
        self._asAdmin()
        new_wflow = {"workflow": self._workflow3.id,
                     "started_by": self._janeDoe.id,
                     "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/activeworkflows/", new_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(ActiveWorkflow.objects.count(), 4)
        self.assertEqual(ActiveWorkflow.objects.filter(workflow=self._workflow3).count(), 2)
        w = ActiveWorkflow.objects.get(workflow=self._workflow3)[1]
        self.assertEqual(w.started_by, self._janeDoe)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 2)
        self._asJaneDoe()
        response = self._client.get('/activeworkflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wflows = response.data
        self.assertEqual(len(wflows["results"]), 4)

    def test_user_edit_own(self):
        self._asJoeBloggs()
        update_wflow = {"started_by": self._joeBloggs.id}
        response = self._client.patch("/activeworkflows/%d/" % self._activeWorkflow1.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's item 4
        self._asJoeBloggs()
        update_wflow = {"started_by": self._joeBloggs.id}
        response = self._client.patch("/activeworkflows/%d/" % self._activeWorkflow3.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_edit_other_readonly(self):
        # Joe can see but not edit Jane's item 3
        self._asJoeBloggs()
        update_wflow = {"started_by": self._joeBloggs.id}
        response = self._client.patch("/activeworkflows/%d/" % self._activeWorkflow2.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's item 1 first so she can edit it
        ViewPermissionsMixin().assign_permissions(instance=self._activeWorkflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        update_wflow = {"started_by": self._joeBloggs.id}
        response = self._client.patch("/activeworkflows/%d/" % self._activeWorkflow1.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_edit_any(self):
        self._asAdmin()
        update_wflow = {"started_by": self._joeBloggs.id}
        response = self._client.patch("/activeworkflows/%d/" % self._activeWorkflow1.id,
                                      update_wflow, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/activeworkflows/%d/" % self._activeWorkflow3.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow3).exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/activeworkflows/%d/" % self._activeWorkflow3.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow3).exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/activeworkflows/%d/" % self._activeWorkflow1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow1).exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._activeWorkflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/activeworkflows/%d/" % self._activeWorkflow1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow1).exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/activeworkflows/%d/" % self._activeWorkflow1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow1).exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own sets
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch(
            "/activeworkflows/%d/set_permissions/" % self._activeWorkflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
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
            "/activeworkflows/%d/set_permissions/" % self._activeWorkflow3.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        w = ActiveWorkflow.objects.get(workflow=self._workflow3)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch(
            "/activeworkflows/%d/set_permissions/" % self._activeWorkflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._activeWorkflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/activeworkflows/%d/set_permissions/" % self._activeWorkflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
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
            "/activeworkflows/%d/set_permissions/" % self._activeWorkflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
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
            "/activeworkflows/%d/set_permissions/" % self._activeWorkflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch(
            "/activeworkflows/%d/set_permissions/" % self._activeWorkflow1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the permission wasn't changed accidentally in the process
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
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
            "/activeworkflows/%d/remove_permissions/?groups=joe_group" % self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's item 4
        self._asJoeBloggs()
        response = self._client.delete(
            "/activeworkflows/%d/remove_permissions/?groups=jane_group" % self._activeWorkflow3.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        w = ActiveWorkflow.objects.get(workflow=self._workflow3)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's item 1
        self._asJaneDoe()
        response = self._client.delete(
            "/activeworkflows/%d/remove_permissions/?groups=joe_group" % self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._activeWorkflow1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/activeworkflows/%d/remove_permissions/?groups=joe_group" % self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=w,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/activeworkflows/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
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
            "/activeworkflows/%d/remove_permissions/?groups=jim_group" %
            self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_add_product_no_id(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/add_product/",
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide a product ID")

    def test_add_product_invalid_id(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/add_product/?id=%d" % (self._activeWorkflow1.id, 99999),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Product with the id %d does not exist" % 99999)

    def test_add_product(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/add_product/?id=%d" % (
                self._activeWorkflow1.id, self._janeDoeProduct.id),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        w = ActiveWorkflow.objects.get(workflow=self._workflow1)
        self.assertEqual(w.product_statuses.count(), 3)
        self.assertEqual(w.product_statuses.all()[2].product, self._janeDoeProduct)

    def test_remove_product_no_id(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/remove_product/",
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide a workflow product ID")

    def test_remove_product_invalid_id(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/remove_product/?id=%d" % (self._activeWorkflow1.id, 99999),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"],
                         "Workflow product with the id %d does not exist" % 99999)

    def test_remove_product(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/remove_product/?id=%d" % (
                self._activeWorkflow1.id, self._workflowProductJoe.id),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Deleting the last item should also have deleted the workflow itself
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow1).exists(), False)

    def test_switch_workflow_no_product(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/switch_workflow/" %
            self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide a workflow product ID")

    def test_switch_workflow_invalid_product(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/switch_workflow/?id=%d&workflow_id=%d" % (
                self._activeWorkflow1.id, 99999, 1234),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"],
                         "Workflow product with the id %d does not exist" % 99999)

    def test_switch_workflow_no_source_or_target(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/switch_workflow/?id=%d" % (
                self._activeWorkflow1.id, self._workflowProductJoe.id),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide a workflow product ID")

    def test_switch_workflow_invalid_target_workflow(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/switch_workflow/?id=%d&workflow_id=%d" % (
                self._activeWorkflow1.id, self._workflowProductJoe.id, 1234),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Workflow with the id %d does not exist" % 1234)

    def test_switch_workflow_invalid_target_activeworkflow(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/switch_workflow/?id=%d&active_workflow_id=%d" % (
                self._activeWorkflow1.id, self._workflowProductJoe.id, 1234),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"],
                         "Active workflow with the id %d does not exist" % 1234)

    def test_switch_workflow_to_workflow(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/switch_workflow/?id=%d&workflow_id=%d" % (
                self._activeWorkflow1.id, self._workflowProductJoe.id, self._workflow2.id),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Test is found in active 2
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow2).all()[0].
                      product_statuses.filter(id=self._workflowProductJoe.id).exists(), True)
        # Test active 1 now one less because empty
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow1).count(), 1)

    def test_switch_workflow_to_active_workflow(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/switch_workflow/?id=%d&active_workflow_id=%d" % (
                self._activeWorkflow1.id, self._workflowProductJoe.id, self._activeWorkflow2.id),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Test is found in active 2
        self.assertIs(ActiveWorkflow.objects.get(workflow=self._workflow2).product_statuses.filter(
            id=self._workflowProductJoe.id).exists(), True)
        # Test active 1 now one less because empty
        self.assertIs(ActiveWorkflow.objects.filter(workflow=self._workflow1).count(), 1)

    def _prepare_start_task(self):
        # results in identifier (Item.identifier) -> data map, data is header->value map
        # File rows: "xxx identifier"+"xxx amount" where xxx is arbitrary and identifier
        # is Item identifier
        # Or: "product input amount" which will override the field above
        #   self._inputTempl   self._item1 / 2 / 3   10 / 20 / 30   i1 / 2 / 3
        #        input_field.inventory_identifier = Item.identifier
        # then run through .task.input_fields[] and add amounts for any that not expected from
        # file and not set by file (matching input_field label to identifier field label in file)
        # and throw error if any are expectd from file
        #   self._inputField1 / 2
        return {"task": {"id": self._task3.id,
                         "product_input": self._prodinput.name,
                         "product_input_amount": 1.0,
                         "product_input_measure": self._millilitre.symbol,
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
                         'labware_identifier': [],
                         'calculation_fields': [],
                         'step_fields': [],
                         'variable_fields': [],
                         },
                "products": [{"product": self._jimBeamProduct.id}],
                "input_files": []  # array of {name,file}
                }

    def test_start_task_preview(self):
        start_task = self._prepare_start_task()
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post(
            "/activeworkflows/%d/start_task/?is_preview=True" % self._activeWorkflow1.id,
            start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # if preview then return [] of ItemTransferPreviewSerializer
        r = response.data
        i3 = r[0]
        i1 = r[1]
        i2 = r[2]
        self.assertEqual(i3["amount_taken"], 1)
        self.assertEqual(i3["item"]["identifier"], "i3")
        self.assertEqual(i1["amount_taken"], 2)
        self.assertEqual(i1["item"]["identifier"], "i1")
        self.assertEqual(i2["amount_taken"], 3)
        self.assertEqual(i2["item"]["identifier"], "i2")
        # check update WorkflowProduct uuid and active fields for each Product on ActiveWorkflow
        for wp in WorkflowProduct.objects.filter(product=self._jimBeamProduct).all():
            self.assertEqual(wp.run_identifier, '')
            self.assertEqual(wp.task_in_progress, False)
        # check create ItemTransfers per input item
        self.assertEqual(ItemTransfer.objects.count(), 0)
        # check one DataEntry per input product item
        self.assertEqual(DataEntry.objects.count(), 0)
        # check update inventory amounts
        self.assertEqual(Item.objects.get(id=self._item1.id).amount_available, 10)
        self.assertEqual(Item.objects.get(id=self._item2.id).amount_available, 20)
        self.assertEqual(Item.objects.get(id=self._item3.id).amount_available, 30)

    def test_start_task_insufficient_inventory(self):
        start_task = self._prepare_start_task()
        start_task["task"]["product_input_amount"] = 99
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # if not enough amounts then 400 and message:
        #   Inventory item {} ({}) is short of amount by {}'.format(
        #                item.identifier, item.name, missing \n next etc.
        self.assertEqual(response.data["message"],
                         "Inventory item i3 (item_3) is short of amount by 69.0 milliliter")
        # check update WorkflowProduct uuid and active fields for each Product on ActiveWorkflow
        for wp in WorkflowProduct.objects.filter(product=self._jimBeamProduct).all():
            self.assertEqual(wp.run_identifier, '')
            self.assertEqual(wp.task_in_progress, False)
        # check create ItemTransfers per input item
        self.assertEqual(ItemTransfer.objects.count(), 0)
        # check one DataEntry per input product item
        self.assertEqual(DataEntry.objects.count(), 0)
        # check update inventory amounts
        self.assertEqual(Item.objects.get(id=self._item1.id).amount_available, 10)
        self.assertEqual(Item.objects.get(id=self._item2.id).amount_available, 20)
        self.assertEqual(Item.objects.get(id=self._item3.id).amount_available, 30)

    def test_start_task(self):
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # check update WorkflowProduct uuid and active fields for each Product on ActiveWorkflow
        uuid = WorkflowProduct.objects.filter(product=self._jimBeamProduct)[0].run_identifier
        for wp in WorkflowProduct.objects.filter(product=self._jimBeamProduct).all():
            self.assertEqual(wp.run_identifier, uuid)
            self.assertEqual(wp.task_in_progress, True)
        # check create ItemTransfers per input item
        self.assertEqual(ItemTransfer.objects.filter(run_identifier=uuid).count(), 3)
        # check one DataEntry per input product item
        self.assertEqual(DataEntry.objects.filter(run_identifier=uuid).count(), 1)
        # check update inventory amounts
        self.assertEqual(Item.objects.get(id=self._item1.id).amount_available, 8)
        self.assertEqual(Item.objects.get(id=self._item2.id).amount_available, 17)
        self.assertEqual(Item.objects.get(id=self._item3.id).amount_available, 29)

    def test_check_task_status_missing_id(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # Get status and check data response
        wp = WorkflowProduct.objects.filter(product=self._jimBeamProduct)[0]
        response = self._client.get(
            "/activeworkflows/%d/task_status/" % self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"],
                         "You must provide the number of the task and a run identifier")

    def test_check_task_status_invalid_id(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # Get status and check data response
        run_identifier = 99999
        task_number = 88888
        response = self._client.get(
            "/activeworkflows/%d/task_status/?run_identifier=%s&task_number=%d" % (
                self._activeWorkflow1.id, run_identifier, task_number),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"],
                         "You must provide a valid task number and run identifier")

    def test_check_task_status(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # Get status and check data response
        wp = WorkflowProduct.objects.filter(product=self._jimBeamProduct)[0]
        run_identifier = wp.run_identifier
        task_number = wp.current_task
        response = self._client.get(
            "/activeworkflows/%d/task_status/?run_identifier=%s&task_number=%d" % (
                self._activeWorkflow1.id, run_identifier, task_number),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'items': {'P101-2: Product3': [{'fields': [
                             {'label': 'Task input', 'value': 'ExampleStuff 1.0 ml'},
                             {'label': 'input1', 'value': 'i1 2.0 ml'},
                             {'label': 'input2', 'value': 'i2 3.0 ml'}],
                            'product_name': 'P101-2: Product3',
                            'id': self._jimBeamProduct.id,
                            'item_name': 'i3: item_3'}]},
                          'name': 'TaskTempl3'})

    def test_check_task_complete_missing_id(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # Complete task
        response = self._client.post(
            "/activeworkflows/%d/complete_task/" %
                self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide product IDs")

    def test_check_task_complete_invalid_id(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # Complete task
        response = self._client.post(
            "/activeworkflows/%d/complete_task/" %
                self._activeWorkflow1.id, [99999],
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide valid product IDs")

    def test_check_task_complete(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        wp = WorkflowProduct.objects.filter(product=self._jimBeamProduct)[0]
        run_identifier = wp.run_identifier
        task_number = wp.current_task
        # Complete task
        response = self._client.post(
            "/activeworkflows/%d/complete_task/" %
                self._activeWorkflow1.id, [self._jimBeamProduct.id],
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task is complete")
        self.assertEqual(ActiveWorkflow.objects.filter(workflow=self._workflow3).count(), 1)
        its = ItemTransfer.objects.filter(run_identifier=run_identifier, is_addition=False)
        for it in its:
            self.assertIs(it.transfer_complete, True)
        des = DataEntry.objects.filter(run_identifier=run_identifier)
        for de in des:
            self.assertEqual(de.state, 'succeeded')
        itemName = '{} {}'.format(self._jimBeamProduct.product_identifier, self._prodinput.name)
        self.assertEqual(Item.objects.filter(name=itemName).count(), 1)
        item = Item.objects.get(name=itemName)
        self.assertEqual(item.item_type, self._prodinput)
        self.assertIs(item.in_inventory, True)
        self.assertEqual(item.amount_available, 5.0)
        self.assertEqual(item.amount_measure, self._millilitre)
        self.assertEqual(item.location, self._location)
        self.assertEqual(item.added_by, self._joeBloggs)
        self.assertEqual(item.created_from.count(), 1)
        self.assertEqual(ItemTransfer.objects.filter(item=item).count(), 1)
        it = ItemTransfer.objects.get(item=item)
        self.assertEqual(it.amount_taken, 5.0)
        self.assertEqual(it.amount_measure, self._millilitre)
        self.assertEqual(it.run_identifier, run_identifier)
        self.assertIs(it.is_addition, True)
        p = WorkflowProduct.objects.get(product=self._jimBeamProduct)
        self.assertEqual(p.run_identifier, '')
        self.assertEqual(p.task_in_progress, False)
        self.assertEqual(p.current_task, 1)
        # Get status and check complete response
        response = self._client.get(
            "/activeworkflows/%d/task_status/?run_identifier=%s&task_number=%d" % (
                self._activeWorkflow1.id, run_identifier, task_number),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data["message"], "Task complete")

    def test_check_task_retry_missing_id(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # Complete task
        response = self._client.post(
            "/activeworkflows/%d/retry_task/" %
            self._activeWorkflow1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide product IDs")

    def test_check_task_retry_invalid_id(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        # Complete task
        response = self._client.post(
            "/activeworkflows/%d/retry_task/" %
            self._activeWorkflow1.id, [99999],
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You must provide valid product IDs")

    def test_check_task_retry(self):
        # Start a task to get status on
        start_task = self._prepare_start_task()
        self._asJoeBloggs()
        response = self._client.post("/activeworkflows/%d/start_task/" % self._activeWorkflow1.id,
                                     start_task, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task started")
        wp = WorkflowProduct.objects.filter(product=self._jimBeamProduct)[0]
        run_identifier = wp.run_identifier
        task_number = wp.current_task
        # Complete task
        response = self._client.post(
            "/activeworkflows/%d/retry_task/" %
            self._activeWorkflow1.id, [self._jimBeamProduct.id],
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task ready for retry")
        self.assertEqual(ActiveWorkflow.objects.filter(workflow=self._workflow3).count(), 1)
        its = ItemTransfer.objects.filter(run_identifier=run_identifier, is_addition=False)
        for it in its:
            self.assertIs(it.transfer_complete, True)
        des = DataEntry.objects.filter(run_identifier=run_identifier)
        for de in des:
            self.assertEqual(de.state, 'failed')
        itemName = '{} {}'.format(self._jimBeamProduct.product_identifier, self._prodinput.name)
        self.assertEqual(Item.objects.filter(name=itemName).count(), 1)
        item = Item.objects.get(name=itemName)
        self.assertEqual(item.item_type, self._prodinput)
        self.assertIs(item.in_inventory, True)
        self.assertEqual(item.amount_available, 5.0)
        self.assertEqual(item.amount_measure, self._millilitre)
        self.assertEqual(item.location, self._location)
        self.assertEqual(item.added_by, self._joeBloggs)
        self.assertEqual(item.created_from.count(), 1)
        self.assertEqual(ItemTransfer.objects.filter(item=item).count(), 1)
        it = ItemTransfer.objects.get(item=item)
        self.assertEqual(it.amount_taken, 5.0)
        self.assertEqual(it.amount_measure, self._millilitre)
        self.assertEqual(it.run_identifier, run_identifier)
        self.assertIs(it.is_addition, True)
        p = WorkflowProduct.objects.get(product=self._jimBeamProduct)
        self.assertEqual(p.run_identifier, '')
        self.assertEqual(p.task_in_progress, False)
        self.assertEqual(p.current_task, 0)
        # Get status and check complete response
        response = self._client.get(
            "/activeworkflows/%d/task_status/?run_identifier=%s&task_number=%d" % (
                self._activeWorkflow1.id, run_identifier, task_number),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data["message"], "Task complete")