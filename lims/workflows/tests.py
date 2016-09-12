from django.contrib.auth.models import Permission, Group
from rest_framework import status
from lims.shared.loggedintestcase import LoggedInTestCase
from .models import Workflow, TaskTemplate
from lims.filetemplate.models import FileTemplate, FileTemplateField
from lims.inventory.models import Location, ItemType, AmountMeasure
from lims.equipment.models import Equipment
from .views import ViewPermissionsMixin


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

#class CalculationFieldTemplate(LoggedInTestCase):

#class InputFieldTemplateTest(LoggedInTestCase):

#class VariableFieldTemplateTest(LoggedInTestCase):

#class OutputFieldTemplateTest(LoggedInTestCase):

#class StepFieldTemplateTest(LoggedInTestCase):

# TODO  /taskfields/ - ONE SET OF THESE TWO FUNCTIONS PER TASKFIELD TYPE
# TODO /taskfields/<pk>/

# TODO / tasks / < pk > / recalculate /  - DEDICATED TEST CLASS

# TODO /activeworkflows/
# TODO /activeworkflows/<pk>/
# TODO / activeworkflows / < pk > / remove_permissions /
# TODO / activeworkflows / < pk > / set_permissions /

# TODO /activeworkflows/<pk>/add_product/
# TODO /activeworkflows/<pk>/complete_task/
# TODO /activeworkflows/<pk>/remove_product/
# TODO /activeworkflows/<pk>/retry_task/
# TODO /activeworkflows/<pk>/start_task/
# TODO /activeworkflows/<pk>/switch_workflow/
# TODO /activeworkflows/<pk>/task_status/
