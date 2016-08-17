from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient


class LoggedInTestCase(TestCase):
    def setUp(self):
        # These objects are recreated afresh for every test method below.
        # Data updated or created in a test method will not persist to another test method.
        self._client = APIClient()

        self._joeBloggs = User.objects.create_user(username='Joe Bloggs',
                                                   email='joe@tgac.com', password='top_secret')
        self._janeDoe = User.objects.create_user(username='Jane Doe',
                                                 email='jane@tgac.com', password='widget')

    # Utility function to switch user
    def _asJoeBloggs(self):
        self._client.logout()
        self._client.login(username="Joe Bloggs", password="top_secret")

    # Utility function to switch user
    def _asJaneDoe(self):
        self._client.logout()
        self._client.login(username="Jane Doe", password="widget")

    # Utility function to switch user
    def _asAnonymous(self):
        self._client.logout()

    # Utility function to switch user
    def _asInvalid(self):
        self._client.logout()
        self._client.login(username="Non Existent", password="made_up")