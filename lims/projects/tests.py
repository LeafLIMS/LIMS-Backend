from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from django.conf import settings
from django.contrib.auth.models import Permission, Group
from .models import Project, Order
from .views import ViewPermissionsMixin


class ProjectTestCase(LoggedInTestCase):
    # TODO Re-enable DISABLED_ methods once SFDC works in testing mode (check for settings.TESTING)
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

    def DISABLED_test_user_create_own_staff(self):
        # Since only staff (and admin) are permitted to create their own projects, we will make
        # Jane staff too.
        self._janeDoe.groups.add(Group.objects.get(name="staff"))
        self._asJaneDoe()
        new_project = {"name": "Jane's Second Project",
                       "description": "Nobel prize winning idea",
                       "order": self._janeDoeOrder.id,
                       "archive": False,
                       "created_by": self._janeDoe.id,
                       "primary_lab_contact": self._staffUser.id}
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

        # Other user still sees just theirs but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 2)

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

    def DISABLED_test_admin_create_any(self):
        # Admin should be able to create a project on behalf of another user
        self._asAdmin()
        new_project = {"name": "Jane's Second Project",
                       "description": "Nobel prize winning idea",
                       "order": self._janeDoeOrder.id,
                       "archive": False,
                       "created_by": self._janeDoe.id,
                       "primary_lab_contact": self._staffUser.id}
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

        # Other user still sees just theirs but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        projects = response.data
        self.assertEqual(len(projects["results"]), 2)

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

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/projects/%d/remove_permissions/?groups=joe_group" % self._joeBloggsProject.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "r")

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
                                                                        name="joe_group")), "r")

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
                                                                        name="jane_group")), "r")
        self.assertEqual(ViewPermissionsMixin().current_permissions(instance=self._joeBloggsProject,
                                                                    group=Group.objects.get(
                                                                        name="joe_group")), "r")
