from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient


class LoggedInTestCase(TestCase):
    def setUp(self):
        # These objects are recreated afresh for every test method below.
        # Data updated or created in a test method will not persist to another test method.
        self._client = APIClient()

        self._joeBloggs = User.objects.create_user(username='Joe Bloggs',
                                                   email='joe@tgac.com', password='top_secret')
        self._joeBloggs.groups.add(Group.objects.create(name="joe_group"))
        self._janeDoe = User.objects.create_user(username='Jane Doe',
                                                 email='jane@tgac.com', password='widget')
        self._janeDoe.groups.add(Group.objects.create(name="jane_group"))
        self._adminUser = User.objects.create_user(username='Super Man',
                                                   email='superman@tgac.com', password='woggle')
        self._adminUser.groups.add(Group.objects.get(name="admin"))
        # Admin users are also staff for the purposes of permissions.
        self._adminUser.groups.add(Group.objects.get(name="staff"))
        self._staffUser = User.objects.create_user(username='Lab Tech',
                                                   email='labtech@tgac.com', password='wiggle')
        self._staffUser.groups.add(Group.objects.get(name="staff"))

    # Utility function to switch user. Joe is a normal user in group joe_group
    def _asJoeBloggs(self):
        self._client.logout()
        self._client.login(username="Joe Bloggs", password="top_secret")

    # Utility function to switch user. Jane is a user in group jane_group.
    def _asJaneDoe(self):
        self._client.logout()
        self._client.login(username="Jane Doe", password="widget")

    # Utility function to switch user. Admin is an admin user.
    def _asAdmin(self):
        self._client.logout()
        self._client.login(username="Super Man", password="woggle")

    # Utility function to switch user. Staff is a staff user.
    def _asStaff(self):
        self._client.logout()
        self._client.login(username="Lab Tech", password="wiggle")

    # Utility function to switch user
    def _asAnonymous(self):
        self._client.logout()

    # Utility function to switch user
    def _asInvalid(self):
        self._client.logout()
        self._client.login(username="Non Existent", password="made_up")
