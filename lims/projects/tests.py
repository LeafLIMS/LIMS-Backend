from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from django.conf import settings
from django.contrib.auth.models import Permission, Group
from .models import Project, Order, Product, ProductStatus, Item, ItemType, Organism
from lims.inventory.models import AmountMeasure
from .parsers import DesignFileParser
from .views import ViewPermissionsMixin


class ProjectTestCase(LoggedInTestCase):
    # TODO Implement SFDC tests once SFDC works in testing mode (check for settings.TESTING)

    def setUp(self):
        super(ProjectTestCase, self).setUp()

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

        # We also have to give Joe and Jane permission to view, change and delete projects in
        # general.
        self._joeBloggs.user_permissions.add(Permission.objects.get(codename="view_project"))
        self._joeBloggs.user_permissions.add(Permission.objects.get(codename="change_project"))
        self._joeBloggs.user_permissions.add(Permission.objects.get(codename="delete_project"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_project"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="change_project"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="delete_project"))

    def test_presets(self):
        self.assertIs(Project.objects.filter(name="Joe's Project").exists(), True)
        project1 = Project.objects.get(name="Joe's Project")
        self.assertEqual(project1.description, "Awfully interesting")
        self.assertEqual(project1.order, self._joeBloggsOrder)
        self.assertEqual(project1.created_by, self._joeBloggs)
        self.assertIs(project1.archive, False)
        self.assertEqual(project1.primary_lab_contact, self._staffUser)
        self.assertEqual(project1.project_identifier,
                         "{}{}".format(settings.PROJECT_IDENTIFIER_PREFIX, project1.identifier))
        self.assertIs(Project.objects.filter(name="Jane's Project").exists(), True)
        project2 = Project.objects.get(name="Jane's Project")
        self.assertEqual(project2.description, "Even more insightful")
        self.assertEqual(project2.order, self._janeDoeOrder)
        self.assertEqual(project2.created_by, self._janeDoe)
        self.assertIs(project2.archive, True)
        self.assertEqual(project2.primary_lab_contact, self._staffUser)
        self.assertEqual(project2.project_identifier,
                         "{}{}".format(settings.PROJECT_IDENTIFIER_PREFIX, project2.identifier))

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/projects/%d/' % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/projects/%d/' % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see projects in his own group
        self._asJoeBloggs()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 1)
        project1 = projects["results"][0]
        self.assertEqual(project1["name"], "Joe's Project")

    def test_user_list_group(self):
        # Jane can see both because her group has read permission to Joe's project
        self._asJaneDoe()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 2)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/projects/%d/' % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project1 = response.data
        self.assertEqual(project1["name"], "Joe's Project")

    def test_user_view_other(self):
        # Jane's project is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/projects/%d/' % self._janeDoeProject.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's project
        self._asJaneDoe()
        response = self._client.get('/projects/%d/' % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project1 = response.data
        self.assertEqual(project1["name"], "Joe's Project")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/projects/%d/' % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project1 = response.data
        self.assertEqual(project1["name"], "Joe's Project")

    def test_user_create_own_staff(self):
        # Since only staff (and admin) are permitted to create their own projects, we will make
        # Jane staff too.
        self._janeDoe.groups.add(Group.objects.get(name="staff"))
        self._asJaneDoe()
        new_project = {"name": "Jane's Second Project",
                       "description": "Nobel prize winning idea",
                       "order": self._janeDoeOrder.id,
                       "archive": False,
                       "created_by": self._janeDoe.id,
                       "primary_lab_contact": self._staffUser.username,
                       "assign_groups": {"jane_group": "r"}}
        response = self._client.post("/projects/", new_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Project.objects.count(), 3)
        self.assertEqual(self._janeDoeOrder.associated_projects.count(), 2)
        self.assertIs(Project.objects.filter(name="Jane's Second Project").exists(), True)
        project = Project.objects.get(name="Jane's Second Project")
        self.assertEqual(project.description, "Nobel prize winning idea")
        self.assertEqual(project.order, self._janeDoeOrder)
        self.assertEqual(project.created_by, self._janeDoe)
        self.assertIs(project.archive, False)
        self.assertEqual(project.primary_lab_contact, self._staffUser)
        self.assertEqual(project.project_identifier,
                         "{}{}".format(settings.PROJECT_IDENTIFIER_PREFIX, project.identifier))

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 3)

    def test_user_create_own_nonstaff(self):
        # Non-staff users cannot create
        self._asJoeBloggs()
        new_project = {"name": "Joe's Second Project",
                       "description": "Nobel prize winning idea",
                       "order": self._joeBloggsOrder.id,
                       "archive": False,
                       "primary_lab_contact": self._staffUser.id}
        response = self._client.post("/projects/", new_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Project.objects.filter(name="Joe's Second Project").exists(), False)

    def test_user_create_other(self):
        # User should not be able to create a project with another user in the created_by field,
        # even if they are staff
        self._janeDoe.groups.add(Group.objects.get(name="staff"))
        self._asJaneDoe()
        new_project = {"name": "Joe's Second Project",
                       "description": "Nobel prize winning idea",
                       "order": self._joeBloggsOrder.id,
                       "archive": False,
                       "created_by": self._joeBloggs.id,
                       "primary_lab_contact": self._staffUser.id}
        response = self._client.post("/projects/", new_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(Project.objects.filter(name="Joe's Second Project").exists(), False)

    def test_admin_create_any(self):
        # Admin should be able to create a project on behalf of another user
        self._asAdmin()
        new_project = {"name": "Jane's Second Project",
                       "description": "Nobel prize winning idea",
                       "order": self._janeDoeOrder.id,
                       "archive": False,
                       "created_by": self._janeDoe.id,
                       "primary_lab_contact": self._staffUser.username,
                       "assign_groups": {"jane_group": "r"}}
        response = self._client.post("/projects/", new_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Project.objects.count(), 3)
        self.assertEqual(self._janeDoeOrder.associated_projects.count(), 2)
        self.assertIs(Project.objects.filter(name="Jane's Second Project").exists(), True)
        project = Project.objects.get(name="Jane's Second Project")
        self.assertEqual(project.description, "Nobel prize winning idea")
        self.assertEqual(project.order, self._janeDoeOrder)
        self.assertEqual(project.created_by, self._adminUser)
        self.assertIs(project.archive, False)
        self.assertEqual(project.primary_lab_contact, self._staffUser)
        self.assertEqual(project.project_identifier,
                         "{}{}".format(settings.PROJECT_IDENTIFIER_PREFIX, project.identifier))

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 3)

    def test_user_edit_own(self):
        self._asJaneDoe()
        updated_project = {"description": "What a brilliant new idea I just had"}
        response = self._client.patch("/projects/%d/" % self._janeDoeProject.id,
                                      updated_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(Project.objects.filter(name="Jane's Project").exists(), True)
        project = Project.objects.get(name="Jane's Project")
        self.assertEqual(project.description, "What a brilliant new idea I just had")
        self.assertEqual(project.order, self._janeDoeOrder)
        self.assertEqual(project.created_by, self._janeDoe)
        self.assertIs(project.archive, True)
        self.assertEqual(project.primary_lab_contact, self._staffUser)
        self.assertEqual(project.project_identifier,
                         "{}{}".format(settings.PROJECT_IDENTIFIER_PREFIX, project.identifier))

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's project
        self._asJoeBloggs()
        updated_project = {"description": "What a brilliant new idea I just had"}
        response = self._client.patch("/projects/%d/" % self._janeDoeProject.id,
                                      updated_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Project.objects.filter(description="Even more insightful").exists(), True)
        self.assertIs(
            Project.objects.filter(description="What a brilliant new idea I just had").exists(),
            False)

    def test_user_edit_other_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        updated_project = {"description": "What a brilliant new idea I just had"}
        response = self._client.patch("/projects/%d/" % self._joeBloggsProject.id,
                                      updated_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Project.objects.filter(description="Even more insightful").exists(), True)
        self.assertIs(
            Project.objects.filter(description="What a brilliant new idea I just had").exists(),
            False)

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProject,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        updated_project = {"description": "What a brilliant new idea I just had"}
        response = self._client.patch("/projects/%d/" % self._joeBloggsProject.id,
                                      updated_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(Project.objects.filter(name="Joe's Project").exists(), True)
        project = Project.objects.get(name="Joe's Project")
        self.assertEqual(project.description, "What a brilliant new idea I just had")
        self.assertEqual(project.order, self._joeBloggsOrder)
        self.assertEqual(project.created_by, self._joeBloggs)
        self.assertIs(project.archive, False)
        self.assertEqual(project.primary_lab_contact, self._staffUser)
        self.assertEqual(project.project_identifier,
                         "{}{}".format(settings.PROJECT_IDENTIFIER_PREFIX, project.identifier))

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_project = {"description": "What a brilliant new idea I just had"}
        response = self._client.patch("/projects/%d/" % self._janeDoeProject.id,
                                      updated_project, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(Project.objects.filter(name="Jane's Project").exists(), True)
        project = Project.objects.get(name="Jane's Project")
        self.assertEqual(project.description, "What a brilliant new idea I just had")
        self.assertEqual(project.order, self._janeDoeOrder)
        self.assertEqual(project.created_by, self._janeDoe)
        self.assertIs(project.archive, True)
        self.assertEqual(project.primary_lab_contact, self._staffUser)
        self.assertEqual(project.project_identifier,
                         "{}{}".format(settings.PROJECT_IDENTIFIER_PREFIX, project.identifier))

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/projects/%d/" % self._janeDoeProject.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Project.objects.filter(name="Jane's Project").exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/projects/%d/" % self._janeDoeProject.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Project.objects.filter(name="Jane's Project").exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/projects/%d/" % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Project.objects.filter(name="Jane's Project").exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProject,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/projects/%d/" % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Project.objects.filter(name="Joe's Project").exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/projects/%d/" % self._joeBloggsProject.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Project.objects.filter(name="Joe's Project").exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own projects
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch("/projects/%d/set_permissions/" % self._joeBloggsProject.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "rw")
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "rw")

    def test_user_set_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        permissions = {"jane_group": "r"}
        response = self._client.patch("/projects/%d/set_permissions/" % self._janeDoeProject.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._janeDoeProject,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch("/projects/%d/set_permissions/" % self._joeBloggsProject.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProject,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch("/projects/%d/set_permissions/" % self._joeBloggsProject.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "r")
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "r")

    def test_admin_set_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch("/projects/%d/set_permissions/" % self._joeBloggsProject.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "r")
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "r")

    def test_set_permissions_invalid_group(self):
        # An invalid group should throw a 400 data error
        self._asAdmin()
        permissions = {"jim_group": "r"}
        response = self._client.patch("/projects/%d/set_permissions/" % self._joeBloggsProject.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch("/projects/%d/set_permissions/" % self._joeBloggsProject.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the permission wasn't changed accidentally in the process
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "rw")

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/projects/%d/remove_permissions/?groups=joe_group" % self._joeBloggsProject.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        response = self._client.delete(
            "/projects/%d/remove_permissions/?groups=jane_group" % self._janeDoeProject.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._janeDoeProject,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        response = self._client.delete(
            "/projects/%d/remove_permissions/?groups=joe_group" % self._joeBloggsProject.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProject,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/projects/%d/remove_permissions/?groups=joe_group" % self._joeBloggsProject.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/projects/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._joeBloggsProject.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), None)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), None)

    def test_remove_permissions_invalid_group(self):
        # An invalid group name should fail quietly - we don't care if permissions can't be
        # removed as the end result is the same, i.e. that group can't access anything
        self._asAdmin()
        response = self._client.delete(
            "/projects/%d/remove_permissions/?groups=jim_group" %
            self._joeBloggsProject.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)


class WorkLogTestCase(LoggedInTestCase):
    # TODO Implement tests when API becomes available

    def setUp(self):
        super(WorkLogTestCase, self).setUp()


class CommentTestCase(LoggedInTestCase):
    # TODO Implement tests when API becomes available

    def setUp(self):
        super(CommentTestCase, self).setUp()


class ProductStatusTestCase(LoggedInTestCase):
    def test_defaults(self):
        self.assertEqual(ProductStatus.objects.count(), 4)
        self.assertIs(ProductStatus.objects.filter(name="Added").exists(), True)
        self.assertIs(ProductStatus.objects.filter(name="Submitted").exists(), True)
        self.assertIs(ProductStatus.objects.filter(name="Received").exists(), True)
        self.assertIs(ProductStatus.objects.filter(name="In Progress").exists(), True)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/productstatuses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get(
            '/productstatuses/%d/' % ProductStatus.objects.get(name="Added").id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/productstatuses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get(
            '/productstatuses/%d/' % ProductStatus.objects.get(name="Added").id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/productstatuses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        statuses = response.data
        self.assertEqual(len(statuses["results"]), 4)

    def test_user_view_single(self):
        self._asJaneDoe()
        response = self._client.get(
            '/productstatuses/%d/' % ProductStatus.objects.get(name="Added").id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        statuses = response.data
        self.assertEqual(statuses["name"], "Added")

    def test_user_create(self):
        self._asJaneDoe()
        new_status = {"name": "Status 3", "description": "Description 3"}
        response = self._client.post("/productstatuses/", new_status, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProductStatus.objects.count(), 4)

    def test_admin_create(self):
        self._asAdmin()
        new_status = {"name": "Status 3", "description": "Description 3"}
        response = self._client.post("/productstatuses/", new_status, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductStatus.objects.count(), 5)

    def test_user_edit(self):
        old_description = ProductStatus.objects.get(name="Added").description
        self._asJoeBloggs()
        updated_status = {"description": "Blah"}
        response = self._client.patch(
            "/productstatuses/%d/" % ProductStatus.objects.get(name="Added").id,
            updated_status, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProductStatus.objects.get(name="Added").description, old_description)

    def test_admin_edit(self):
        self._asAdmin()
        updated_status = {"description": "Blah"}
        response = self._client.patch(
            "/productstatuses/%d/" % ProductStatus.objects.get(name="Added").id,
            updated_status, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ProductStatus.objects.get(name="Added").description, "Blah")

    def test_user_delete(self):
        self._asJoeBloggs()
        response = self._client.delete(
            "/productstatuses/%d/" % ProductStatus.objects.get(name="Added").id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(ProductStatus.objects.filter(name="Added").exists(), True)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete(
            "/productstatuses/%d/" % ProductStatus.objects.get(name="Added").id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(ProductStatus.objects.filter(name="Added").exists(), False)


class ParserTestCase(LoggedInTestCase):
    def setUp(self):
        super(ParserTestCase, self).setUp()

        itemtype = ItemType.objects.create(name="TestType")
        amountmeasure = AmountMeasure.objects.create(name="TestAmount", symbol="TA")
        item1 = Item.objects.create(name="Item_1", item_type=itemtype, amount_measure=amountmeasure,
                                    added_by=self._joeBloggs)
        item2 = Item.objects.create(name="Item_2", item_type=itemtype, amount_measure=amountmeasure,
                                    added_by=self._joeBloggs)
        item3 = Item.objects.create(name="item_3", item_type=itemtype, amount_measure=amountmeasure,
                                    added_by=self._joeBloggs)
        self._expected_items = [item1, item2, item3]

    def test_csv_parser(self):
        csv = """Name,Description,Role,Color,Sequence,@metadata
Item_1,test,test,test,test,test
Item_2,test,test,test,test,test
item_3,test,test,test,test,test"""
        parser = DesignFileParser(data=csv)
        items = parser.parse_csv()
        self.assertEqual(set(items), set(self._expected_items))

    def test_genbank_parser(self):
        gb = """LOCUS       SCU49845     5028 bp    DNA             PLN       21-JUN-1999
DEFINITION  Saccharomyces cerevisiae TCP1-beta gene, partial cds, and Axl2p
            (AXL2) and Rev7p (REV7) genes, complete cds.
ACCESSION   U49845
VERSION     U49845.1  GI:1293613
KEYWORDS    .
SOURCE      Saccharomyces cerevisiae (baker's yeast)
  ORGANISM  Saccharomyces cerevisiae
            Eukaryota; Fungi; Ascomycota; Saccharomycotina; Saccharomycetes;
            Saccharomycetales; Saccharomycetaceae; Saccharomyces.
REFERENCE   1  (bases 1 to 5028)
  AUTHORS   Torpey,L.E., Gibbs,P.E., Nelson,J. and Lawrence,C.W.
  TITLE     Cloning and sequence of REV7, a gene whose function is required for
            DNA damage-induced mutagenesis in Saccharomyces cerevisiae
  JOURNAL   Yeast 10 (11), 1503-1509 (1994)
  PUBMED    7871890
REFERENCE   2  (bases 1 to 5028)
  AUTHORS   Roemer,T., Madden,K., Chang,J. and Snyder,M.
  TITLE     Selection of axial growth sites in yeast requires Axl2p, a novel
            plasma membrane glycoprotein
  JOURNAL   Genes Dev. 10 (7), 777-793 (1996)
  PUBMED    8846915
REFERENCE   3  (bases 1 to 5028)
  AUTHORS   Roemer,T.
  TITLE     Direct Submission
  JOURNAL   Submitted (22-FEB-1996) Terry Roemer, Biology, Yale University, New
            Haven, CT, USA
FEATURES             Location/Qualifiers
     source          1..5028
                     /organism="Saccharomyces cerevisiae"
                     /db_xref="taxon:4932"
                     /chromosome="IX"
                     /map="9"
     primer_bind     <1..206
                     /label="Item_1"
                     /codon_start=3
                     /product="TCP1-beta"
                     /protein_id="AAA98665.1"
                     /db_xref="GI:1293614"
                     /translation="SSIYNGISTSGLDLNNGTIADMRQLGIVESYKLKRAVVSSASEA
                     AEVLLRVDNIIRARPRTANRQHM"
     gene            687..3158
                     /gene="AXL2"
     3'_utr          687..3158
                     /gene="AXL2"
                     /note="plasma membrane glycoprotein"
                     /codon_start=1
                     /label="Item_2"
                     /function="required for axial budding pattern of S.
                     cerevisiae"
                     /product="Axl2p"
                     /protein_id="AAA98666.1"
                     /db_xref="GI:1293615"
                     /translation="MTQLQISLLLTATISLLHLVVATPYEAYPIGKQYPPVARVNESF
                     TFQISNDTYKSSVDKTAQITYNCFDLPSWLSFDSSSRTFSGEPSSDLLSDANTTLYFN
                     VILEGTDSADSTSLNNTYQFVVTNRPSISLSSDFNLLALLKNYGYTNGKNALKLDPNE
                     VFNVTFDRSMFTNEESIVSYYGRSQLYNAPLPNWLFFDSGELKFTGTAPVINSAIAPE
                     TSYSFVIIATDIEGFSAVEVEFELVIGAHQLTTSIQNSLIINVTDTGNVSYDLPLNYV
                     YLDDDPISSDKLGSINLLDAPDWVALDNATISGSVPDELLGKNSNPANFSVSIYDTYG
                     DVIYFNFEVVSTTDLFAISSLPNINATRGEWFSYYFLPSQFTDYVNTNVSLEFTNSSQ
                     DHDWVKFQSSNLTLAGEVPKNFDKLSLGLKANQGSQSQELYFNIIGMDSKITHSNHSA
                     NATSTRSSHHSTSTSSYTSSTYTAKISSTSAAATSSAPAALPAANKTSSHNKKAVAIA
                     CGVAIPLGVILVALICFLIFWRRRRENPDDENLPHAISGPDLNNPANKPNQENATPLN
                     NPFDDDASSYDDTSIARRLAALNTLKLDNHSATESDISSVDEKRDSLSGMNTYNDQFQ
                     SQSKEELLAKPPVQPPESPFFDPQNRSSSVYMDSEPAVNKSWRYTGNLSPVSDIVRDS
                     YGSQKTVDTEKLFDLEAPEKEKRTSRDVTMSSLDPWNSNISPSPVRKSVTPSPYNVTK
                     HRNRHLQNIQDSQSGKNGITPTTMSTSSSDDFVPVKDGENFCWVHSMEPDRRPSKKRL
                     VDFSNKSNVNVGQVKDIHGRIPEML"
     gene            complement(3300..4037)
                     /gene="REV7"
     CDS             complement(3300..4037)
                     /gene="REV7"
                     /label="item_3"
                     /codon_start=1
                     /product="Rev7p"
                     /protein_id="AAA98667.1"
                     /db_xref="GI:1293616"
                     /translation="MNRWVEKWLRVYLKCYINLILFYRNVYPPQSFDYTTYQSFNLPQ
                     FVPINRHPALIDYIEELILDVLSKLTHVYRFSICIINKKNDLCIEKYVLDFSELQHVD
                     KDDQIITETEVFDEFRSSLNSLIMHLEKLPKVNDDTITFEAVINAIELELGHKLDRNR
                     RVDSLEEKAEIERDSNWVKCQEDENLPDNNGFQPPKIKLTSLVGSDVGPLIIHQFSEK
                     LISGDDKILNGVYSQYEEGESIFGSLF"
ORIGIN
        1 gatcctccat atacaacggt atctccacct caggtttaga tctcaacaac ggaaccattg
       61 ccgacatgag acagttaggt atcgtcgaga gttacaagct aaaacgagca gtagtcagct
      121 ctgcatctga agccgctgaa gttctactaa gggtggataa catcatccgt gcaagaccaa
      181 gaaccgccaa tagacaacat atgtaacata tttaggatat acctcgaaaa taataaaccg
      241 ccacactgtc attattataa ttagaaacag aacgcaaaaa ttatccacta tataattcaa
      301 agacgcgaaa aaaaaagaac aacgcgtcat agaacttttg gcaattcgcg tcacaaataa
      361 attttggcaa cttatgtttc ctcttcgagc agtactcgag ccctgtctca agaatgtaat
      421 aatacccatc gtaggtatgg ttaaagatag catctccaca acctcaaagc tccttgccga
      481 gagtcgccct cctttgtcga gtaattttca cttttcatat gagaacttat tttcttattc
      541 tttactctca catcctgtag tgattgacac tgcaacagcc accatcacta gaagaacaga
      601 acaattactt aatagaaaaa ttatatcttc ctcgaaacga tttcctgctt ccaacatcta
      661 cgtatatcaa gaagcattca cttaccatga cacagcttca gatttcatta ttgctgacag
      721 ctactatatc actactccat ctagtagtgg ccacgcccta tgaggcatat cctatcggaa
      781 aacaataccc cccagtggca agagtcaatg aatcgtttac atttcaaatt tccaatgata
      841 cctataaatc gtctgtagac aagacagctc aaataacata caattgcttc gacttaccga
      901 gctggctttc gtttgactct agttctagaa cgttctcagg tgaaccttct tctgacttac
      961 tatctgatgc gaacaccacg ttgtatttca atgtaatact cgagggtacg gactctgccg
     1021 acagcacgtc tttgaacaat acataccaat ttgttgttac aaaccgtcca tccatctcgc
     1081 tatcgtcaga tttcaatcta ttggcgttgt taaaaaacta tggttatact aacggcaaaa
     1141 acgctctgaa actagatcct aatgaagtct tcaacgtgac ttttgaccgt tcaatgttca
     1201 ctaacgaaga atccattgtg tcgtattacg gacgttctca gttgtataat gcgccgttac
     1261 ccaattggct gttcttcgat tctggcgagt tgaagtttac tgggacggca ccggtgataa
     1321 actcggcgat tgctccagaa acaagctaca gttttgtcat catcgctaca gacattgaag
     1381 gattttctgc cgttgaggta gaattcgaat tagtcatcgg ggctcaccag ttaactacct
     1441 ctattcaaaa tagtttgata atcaacgtta ctgacacagg taacgtttca tatgacttac
     1501 ctctaaacta tgtttatctc gatgacgatc ctatttcttc tgataaattg ggttctataa
     1561 acttattgga tgctccagac tgggtggcat tagataatgc taccatttcc gggtctgtcc
     1621 cagatgaatt actcggtaag aactccaatc ctgccaattt ttctgtgtcc atttatgata
     1681 cttatggtga tgtgatttat ttcaacttcg aagttgtctc cacaacggat ttgtttgcca
     1741 ttagttctct tcccaatatt aacgctacaa ggggtgaatg gttctcctac tattttttgc
     1801 cttctcagtt tacagactac gtgaatacaa acgtttcatt agagtttact aattcaagcc
     1861 aagaccatga ctgggtgaaa ttccaatcat ctaatttaac attagctgga gaagtgccca
     1921 agaatttcga caagctttca ttaggtttga aagcgaacca aggttcacaa tctcaagagc
     1981 tatattttaa catcattggc atggattcaa agataactca ctcaaaccac agtgcgaatg
     2041 caacgtccac aagaagttct caccactcca cctcaacaag ttcttacaca tcttctactt
     2101 acactgcaaa aatttcttct acctccgctg ctgctacttc ttctgctcca gcagcgctgc
     2161 cagcagccaa taaaacttca tctcacaata aaaaagcagt agcaattgcg tgcggtgttg
     2221 ctatcccatt aggcgttatc ctagtagctc tcatttgctt cctaatattc tggagacgca
     2281 gaagggaaaa tccagacgat gaaaacttac cgcatgctat tagtggacct gatttgaata
     2341 atcctgcaaa taaaccaaat caagaaaacg ctacaccttt gaacaacccc tttgatgatg
     2401 atgcttcctc gtacgatgat acttcaatag caagaagatt ggctgctttg aacactttga
     2461 aattggataa ccactctgcc actgaatctg atatttccag cgtggatgaa aagagagatt
     2521 ctctatcagg tatgaataca tacaatgatc agttccaatc ccaaagtaaa gaagaattat
     2581 tagcaaaacc cccagtacag cctccagaga gcccgttctt tgacccacag aataggtctt
     2641 cttctgtgta tatggatagt gaaccagcag taaataaatc ctggcgatat actggcaacc
     2701 tgtcaccagt ctctgatatt gtcagagaca gttacggatc acaaaaaact gttgatacag
     2761 aaaaactttt cgatttagaa gcaccagaga aggaaaaacg tacgtcaagg gatgtcacta
     2821 tgtcttcact ggacccttgg aacagcaata ttagcccttc tcccgtaaga aaatcagtaa
     2881 caccatcacc atataacgta acgaagcatc gtaaccgcca cttacaaaat attcaagact
     2941 ctcaaagcgg taaaaacgga atcactccca caacaatgtc aacttcatct tctgacgatt
     3001 ttgttccggt taaagatggt gaaaattttt gctgggtcca tagcatggaa ccagacagaa
     3061 gaccaagtaa gaaaaggtta gtagattttt caaataagag taatgtcaat gttggtcaag
     3121 ttaaggacat tcacggacgc atcccagaaa tgctgtgatt atacgcaacg atattttgct
     3181 taattttatt ttcctgtttt attttttatt agtggtttac agatacccta tattttattt
     3241 agtttttata cttagagaca tttaatttta attccattct tcaaatttca tttttgcact
     3301 taaaacaaag atccaaaaat gctctcgccc tcttcatatt gagaatacac tccattcaaa
     3361 attttgtcgt caccgctgat taatttttca ctaaactgat gaataatcaa aggccccacg
     3421 tcagaaccga ctaaagaagt gagttttatt ttaggaggtt gaaaaccatt attgtctggt
     3481 aaattttcat cttcttgaca tttaacccag tttgaatccc tttcaatttc tgctttttcc
     3541 tccaaactat cgaccctcct gtttctgtcc aacttatgtc ctagttccaa ttcgatcgca
     3601 ttaataactg cttcaaatgt tattgtgtca tcgttgactt taggtaattt ctccaaatgc
     3661 ataatcaaac tatttaagga agatcggaat tcgtcgaaca cttcagtttc cgtaatgatc
     3721 tgatcgtctt tatccacatg ttgtaattca ctaaaatcta aaacgtattt ttcaatgcat
     3781 aaatcgttct ttttattaat aatgcagatg gaaaatctgt aaacgtgcgt taatttagaa
     3841 agaacatcca gtataagttc ttctatatag tcaattaaag caggatgcct attaatggga
     3901 acgaactgcg gcaagttgaa tgactggtaa gtagtgtagt cgaatgactg aggtgggtat
     3961 acatttctat aaaataaaat caaattaatg tagcatttta agtataccct cagccacttc
     4021 tctacccatc tattcataaa gctgacgcaa cgattactat tttttttttc ttcttggatc
     4081 tcagtcgtcg caaaaacgta taccttcttt ttccgacctt ttttttagct ttctggaaaa
     4141 gtttatatta gttaaacagg gtctagtctt agtgtgaaag ctagtggttt cgattgactg
     4201 atattaagaa agtggaaatt aaattagtag tgtagacgta tatgcatatg tatttctcgc
     4261 ctgtttatgt ttctacgtac ttttgattta tagcaagggg aaaagaaata catactattt
     4321 tttggtaaag gtgaaagcat aatgtaaaag ctagaataaa atggacgaaa taaagagagg
     4381 cttagttcat cttttttcca aaaagcaccc aatgataata actaaaatga aaaggatttg
     4441 ccatctgtca gcaacatcag ttgtgtgagc aataataaaa tcatcacctc cgttgccttt
     4501 agcgcgtttg tcgtttgtat cttccgtaat tttagtctta tcaatgggaa tcataaattt
     4561 tccaatgaat tagcaatttc gtccaattct ttttgagctt cttcatattt gctttggaat
     4621 tcttcgcact tcttttccca ttcatctctt tcttcttcca aagcaacgat ccttctaccc
     4681 atttgctcag agttcaaatc ggcctctttc agtttatcca ttgcttcctt cagtttggct
     4741 tcactgtctt ctagctgttg ttctagatcc tggtttttct tggtgtagtt ctcattatta
     4801 gatctcaagt tattggagtc ttcagccaat tgctttgtat cagacaattg actctctaac
     4861 ttctccactt cactgtcgag ttgctcgttt ttagcggaca aagatttaat ctcgttttct
     4921 ttttcagtgt tagattgctc taattctttg agctgttctc tcagctcctc atatttttct
     4981 tgccatgact cagattctaa ttttaagcta ttcaatttct ctttgatc
//"""
        parser = DesignFileParser(data=gb)
        items = parser.parse_gb()
        self.assertEqual(set(items), set(self._expected_items))


class ProductTestCase(LoggedInTestCase):
    def setUp(self):
        super(ProductTestCase, self).setUp()

        self._human = Organism.objects.create(name="Homo sapiens", common_name="Human")
        self._mouse = Organism.objects.create(name="Mus musculus", common_name="Mouse")
        self._itemtype = ItemType.objects.create(name="TestType")
        self._amountmeasure = AmountMeasure.objects.create(name="TestAmount", symbol="TA")
        item1 = Item.objects.create(name="Item_1", item_type=self._itemtype,
                                    amount_measure=self._amountmeasure,
                                    added_by=self._joeBloggs)
        item2 = Item.objects.create(name="Item_2", item_type=self._itemtype,
                                    amount_measure=self._amountmeasure,
                                    added_by=self._joeBloggs)
        item3 = Item.objects.create(name="item_3", item_type=self._itemtype,
                                    amount_measure=self._amountmeasure,
                                    added_by=self._joeBloggs)
        self._expecteditems = [item1, item2, item3]

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
                                   product_type=self._itemtype,
                                   optimised_for=self._human,
                                   created_by=self._joeBloggs,
                                   project=self._joeBloggsProject)
        self._janeDoeProduct = \
            Product.objects.create(name="Product2", status=ProductStatus.objects.get(name="Added"),
                                   product_type=self._itemtype,
                                   optimised_for=self._human,
                                   created_by=self._janeDoe,
                                   project=self._janeDoeProject)

        # We have to simulate giving Joe and Jane's groups access to these products. Joe can see and
        # edit only his.
        # Jane can see and edit hers, and see Joe's but not edit it.
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProduct,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._janeDoeProduct,
                                                  permissions={"jane_group": "rw"})

    def test_presets(self):
        self.assertIs(Product.objects.filter(name="Product1").exists(), True)
        product1 = Product.objects.get(name="Product1")
        self.assertEqual(product1.product_identifier,
                         '{}-{}'.format(product1.project.project_identifier, product1.identifier))
        self.assertEqual(product1.product_type, self._itemtype)
        self.assertEqual(product1.optimised_for, self._human)
        self.assertEqual(product1.created_by, self._joeBloggs)
        self.assertEqual(product1.project, self._joeBloggsProject)
        self.assertIs(Product.objects.filter(name="Product2").exists(), True)
        product2 = Product.objects.get(name="Product2")
        self.assertEqual(product2.product_identifier,
                         '{}-{}'.format(product2.project.project_identifier, product2.identifier))
        self.assertEqual(product2.product_type, self._itemtype)
        self.assertEqual(product2.optimised_for, self._human)
        self.assertEqual(product2.created_by, self._janeDoe)
        self.assertEqual(product2.project, self._janeDoeProject)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/products/%d/' % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/products/%d/' % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see products in his own group
        self._asJoeBloggs()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data
        self.assertEqual(len(products["results"]), 1)
        product1 = products["results"][0]
        self.assertEqual(product1["name"], "Product1")

    def test_user_list_group(self):
        # Jane can see both because her group has read permission to Joe's project
        self._asJaneDoe()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data
        self.assertEqual(len(products["results"]), 2)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/products/%d/' % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product1 = response.data
        self.assertEqual(product1["name"], "Product1")

    def test_user_view_other(self):
        # Jane's project is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/products/%d/' % self._janeDoeProduct.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's project
        self._asJaneDoe()
        response = self._client.get('/products/%d/' % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product1 = response.data
        self.assertEqual(product1["name"], "Product1")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data
        self.assertEqual(len(products["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/products/%d/' % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product1 = response.data
        self.assertEqual(product1["name"], "Product1")

    def test_user_create_own_staff(self):
        # Since only staff (and admin) are permitted to create their own products, we will make
        # Jane staff too.
        self._janeDoe.groups.add(Group.objects.get(name="staff"))
        self._asJaneDoe()
        new_product = {"name": "Product3",
                       "status": "Added",
                       "product_type": self._itemtype.name,
                       "optimised_for": self._human.name,
                       "created_by": self._janeDoe.id,
                       "project": self._janeDoeProject.id,
                       "assign_groups": {"jane_group": "r"},
                       "design_format": "csv",
                       "design": """Name,Description,Role,Color,Sequence,@metadata
Item_1,test,test,test,test,test
Item_2,test,test,test,test,test
item_3,test,test,test,test,test"""}
        response = self._client.post("/products/", new_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # TEST ERR 400

        self.assertEqual(Product.objects.count(), 3)
        self.assertIs(Product.objects.filter(name="Product3").exists(), True)
        product = Product.objects.get(name="Product3")
        self.assertEqual(set(product.linked_inventory.all()), set(self._expecteditems))
        self.assertEqual(product.status, ProductStatus.objects.get(name="Added"))
        self.assertEqual(product.product_type, self._itemtype)
        self.assertEqual(product.optimised_for, self._human)
        self.assertEqual(product.created_by, self._janeDoe)
        self.assertEqual(product.project, self._janeDoeProject)
        self.assertEqual(product.design_format, "csv")
        self.assertEqual(product.product_identifier,
                         '{}-{}'.format(product.project.project_identifier, product.identifier))

        # Other user still sees just theirs but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data
        self.assertEqual(len(products["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data
        self.assertEqual(len(products["results"]), 3)

    def test_user_create_own_nonstaff(self):
        # Non-staff users cannot create
        self._asJoeBloggs()
        new_product = {"name": "Product3",
                       "status": "Added",
                       "product_type": self._itemtype.name,
                       "optimised_for": self._human.name,
                       "created_by": self._joeBloggs.id,
                       "project": self._joeBloggsProject.id,
                       "assign_groups": {"joe_group": "r"},
                       "design_format": "csv",
                       "design": """Name,Description,Role,Color,Sequence,@metadata
Item_1,test,test,test,test,test
Item_2,test,test,test,test,test
item_3,test,test,test,test,test"""}
        response = self._client.post("/products/", new_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Product.objects.filter(name="Product3").exists(), False)

    def test_user_create_other_user(self):
        # User should not be able to create a product with another user in the created_by field,
        # even if they are staff
        self._janeDoe.groups.add(Group.objects.get(name="staff"))
        self._asJaneDoe()
        new_product = {"name": "Product3",
                       "status": "Added",
                       "product_type": self._itemtype.name,
                       "optimised_for": self._human.name,
                       "created_by": self._joeBloggs.id,
                       "project": self._joeBloggsProject.id,
                       "assign_groups": {"jane_group": "r"},
                       "design_format": "csv",
                       "design": """Name,Description,Role,Color,Sequence,@metadata
Item_1,test,test,test,test,test
Item_2,test,test,test,test,test
item_3,test,test,test,test,test"""}
        response = self._client.post("/products/", new_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(Product.objects.filter(name="Product3").exists(), False)

    def test_user_create_other_product_readonly(self):
        # User should not be able to create a product for another user's project even if staff, if
        # they are read-only or otherwise not in a read-write group for that project
        self._janeDoe.groups.add(Group.objects.get(name="staff"))
        self._asJaneDoe()
        new_product = {"name": "Product3",
                       "status": "Added",
                       "product_type": self._itemtype.name,
                       "optimised_for": self._human.name,
                       "created_by": self._janeDoe.id,
                       "project": self._joeBloggsProject.id,
                       "assign_groups": {"jane_group": "r"},
                       "design_format": "csv",
                       "design": """Name,Description,Role,Color,Sequence,@metadata
Item_1,test,test,test,test,test
Item_2,test,test,test,test,test
item_3,test,test,test,test,test"""}
        response = self._client.post("/products/", new_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(Product.objects.filter(name="Product3").exists(), False)

    def test_user_create_other_product_readwrite(self):
        # User should  be able to create a product for another user's project if they are
        # staff and in the read-write group for that project.
        # Fake them being in the read-write group by adding them now.
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProject,
                                                  permissions={"jane_group": "rw"})
        self._janeDoe.groups.add(Group.objects.get(name="staff"))
        self._asJaneDoe()
        new_product = {"name": "Product3",
                       "status": "Added",
                       "product_type": self._itemtype.name,
                       "optimised_for": self._human.name,
                       "created_by": self._janeDoe.id,
                       "project": self._joeBloggsProject.id,
                       "assign_groups": {"jane_group": "r"},
                       "design_format": "csv",
                       "design": """Name,Description,Role,Color,Sequence,@metadata
Item_1,test,test,test,test,test
Item_2,test,test,test,test,test
item_3,test,test,test,test,test"""}
        response = self._client.post("/products/", new_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # TEST ERR 400

        self.assertEqual(Product.objects.count(), 3)
        self.assertIs(Product.objects.filter(name="Product3").exists(), True)

    def test_admin_create_any(self):
        # Admin should be able to create a project on behalf of another user
        self._asAdmin()
        new_product = {"name": "Product3",
                       "status": "Added",
                       "product_type": self._itemtype.name,
                       "optimised_for": self._human.name,
                       "created_by": self._janeDoe.id,
                       "project": self._janeDoeProject.id,
                       "assign_groups": {"jane_group": "r"},
                       "design_format": "csv",
                       "design": """Name,Description,Role,Color,Sequence,@metadata
Item_1,test,test,test,test,test
Item_2,test,test,test,test,test
item_3,test,test,test,test,test"""}
        response = self._client.post("/products/", new_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # TODO ERR 400

        self.assertEqual(Product.objects.count(), 3)
        self.assertIs(Product.objects.filter(name="Product3").exists(), True)
        product = Product.objects.get(name="Product3")
        self.assertEqual(set(product.linked_inventory.all()), set(self._expecteditems))
        self.assertEqual(product.status, ProductStatus.objects.get(name="Added"))
        self.assertEqual(product.product_type, self._itemtype)
        self.assertEqual(product.optimised_for, self._human)
        self.assertEqual(product.created_by, self._adminUser)
        self.assertEqual(product.project, self._janeDoeProject)
        self.assertEqual(product.design_format, "csv")
        self.assertEqual(product.product_identifier,
                         '{}-{}'.format(product.project.project_identifier, product.identifier))

        # Other user still sees just theirs but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data
        self.assertEqual(len(products["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.data
        self.assertEqual(len(products["results"]), 2)

    def test_user_edit_own(self):
        self._asJaneDoe()
        updated_product = {"optimised_for": self._mouse.name}
        response = self._client.patch("/products/%d/" % self._janeDoeProduct.id,
                                      updated_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # TEST ERR 400
        product = Product.objects.get(name="Product2")
        self.assertEqual(product.optimised_for, self._mouse)

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's project
        self._asJoeBloggs()
        updated_product = {"optimised_for": self._mouse.name}
        response = self._client.patch("/products/%d/" % self._janeDoeProduct.id,
                                      updated_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Product.objects.filter(optimised_for=self._mouse).exists(), False)

    def test_user_edit_other_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        updated_product = {"optimised_for": self._mouse.name}
        response = self._client.patch("/products/%d/" % self._joeBloggsProduct.id,
                                      updated_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Product.objects.filter(optimised_for=self._mouse).exists(), False)

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can edit it
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProduct,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        updated_product = {"optimised_for": self._mouse.name}
        response = self._client.patch("/products/%d/" % self._joeBloggsProduct.id,
                                      updated_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # TEST ERR 400
        product = Product.objects.get(name="Product1")
        self.assertEqual(product.optimised_for, self._mouse)

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_product = {"optimised_for": self._mouse.name}
        response = self._client.patch("/products/%d/" % self._joeBloggsProduct.id,
                                      updated_product, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # TODO ERR 400
        product = Product.objects.get(name="Product1")
        self.assertEqual(product.optimised_for, self._mouse)

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/products/%d/" % self._janeDoeProduct.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Product.objects.filter(name="Product2").exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/products/%d/" % self._janeDoeProduct.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Product.objects.filter(name="Product2").exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/products/%d/" % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Product.objects.filter(name="Product1").exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProduct,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/products/%d/" % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Product.objects.filter(name="Product1").exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/products/%d/" % self._joeBloggsProduct.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Product.objects.filter(name="Product1").exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own projects
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch("/products/%d/set_permissions/" % self._joeBloggsProduct.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "rw")
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "rw")

    def test_user_set_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        permissions = {"jane_group": "r"}
        response = self._client.patch("/products/%d/set_permissions/" % self._janeDoeProduct.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._janeDoeProduct,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch("/products/%d/set_permissions/" % self._joeBloggsProduct.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProduct,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch("/products/%d/set_permissions/" % self._joeBloggsProduct.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "r")
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "r")

    def test_admin_set_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch("/products/%d/set_permissions/" % self._joeBloggsProduct.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "r")
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "r")

    def test_set_permissions_invalid_group(self):
        # An invalid group should throw a 400 data error
        self._asAdmin()
        permissions = {"jim_group": "r"}
        response = self._client.patch("/products/%d/set_permissions/" % self._joeBloggsProduct.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch("/products/%d/set_permissions/" % self._joeBloggsProduct.id,
                                      permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # TODO ERR 400
        # Check the permission wasn't changed accidentally in the process
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "rw")

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/products/%d/remove_permissions/?groups=joe_group" % self._joeBloggsProduct.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        response = self._client.delete(
            "/products/%d/remove_permissions/?groups=jane_group" % self._janeDoeProduct.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._janeDoeProduct,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        response = self._client.delete(
            "/products/%d/remove_permissions/?groups=joe_group" % self._joeBloggsProduct.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._joeBloggsProduct,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/products/%d/remove_permissions/?groups=joe_group" % self._joeBloggsProduct.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/products/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._joeBloggsProduct.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="jane_group")), None)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProduct,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), None)

    def test_remove_permissions_invalid_group(self):
        # An invalid group name should fail quietly - we don't care if permissions can't be
        # removed as the end result is the same, i.e. that group can't access anything
        self._asAdmin()
        response = self._client.delete(
            "/products/%d/remove_permissions/?groups=jim_group" %
            self._joeBloggsProduct.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)
