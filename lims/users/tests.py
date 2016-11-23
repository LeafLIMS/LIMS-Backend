from django.contrib.auth.models import User, Group, Permission
from lims.addressbook.models import Address
from lims.shared.loggedintestcase import LoggedInTestCase
from django.contrib.auth.hashers import check_password
from rest_framework import status


class UserTestCase(LoggedInTestCase):
    def setUp(self):
        super(UserTestCase, self).setUp()
        # No need to define any other users as we have them from LoggedInTestCase already
        # Add extra details to one existing user
        self._joeBloggs.first_name = "Joe"
        self._joeBloggs.last_name = "Bloggs"
        self._joeBloggsAddress = Address.objects.create(institution_name="Beetroot Institute",
                                                        address_1="12 Muddy Field",
                                                        address_2="Long Lane",
                                                        city="Norwich",
                                                        postcode="NR1 1AA",
                                                        country="UK",
                                                        user=self._joeBloggs)
        self._joeBloggs.addresses.add(self._joeBloggsAddress)
        self._joeBloggs.save()

    def test_presets(self):
        self.assertIs(User.objects.filter(username="Joe Bloggs").exists(), True)
        user1 = User.objects.get(username="Joe Bloggs")
        self.assertEqual(user1.email, "joe@tgac.com")
        self.assertEqual(user1.first_name, "Joe")
        self.assertEqual(user1.last_name, "Bloggs")
        self.assertEqual(user1.addresses.count(), 1)
        self.assertEqual(user1.addresses.all()[0], self._joeBloggsAddress)
        self.assertEqual(user1.groups.count(), 1)
        self.assertEqual(user1.groups.all()[0], Group.objects.get(name="joe_group"))
        self.assertIs(User.objects.filter(username="Jane Doe").exists(), True)
        user1 = User.objects.get(username="Jane Doe")
        self.assertEqual(user1.email, "jane@tgac.com")
        self.assertEqual(User.objects.count(), 5)  # 4 presets plus default Anonymous user

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/users/%d/' % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/users/%d/' % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Others not permitted
        self._asJoeBloggs()
        response = self._client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data
        self.assertEqual(len(users["results"]), 1)
        user1 = users["results"][0]
        self.assertEqual(user1["username"], "Joe Bloggs")

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/users/%d/' % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1 = response.data
        self.assertEqual(user1["username"], "Joe Bloggs")
        self.assertEqual(user1["email"], "joe@tgac.com")
        self.assertEqual(user1["first_name"], "Joe")
        self.assertEqual(user1["last_name"], "Bloggs")
        addresses = user1["addresses"]
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0]["institution_name"], "Beetroot Institute")
        groups = user1["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0], "joe_group")

    def test_user_view_other(self):
        # Others not permitted
        self._asJaneDoe()
        response = self._client.get('/users/%d/' % self._janeDoe.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._client.get('/users/%d/' % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data
        self.assertEqual(len(users["results"]), 5)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/users/%d/' % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1 = response.data
        self.assertEqual(user1["username"], "Joe Bloggs")
        self.assertEqual(user1["email"], "joe@tgac.com")
        self.assertEqual(user1["first_name"], "Joe")
        self.assertEqual(user1["last_name"], "Bloggs")
        addresses = user1["addresses"]
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0]["institution_name"], "Beetroot Institute")
        groups = user1["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0], "joe_group")

    def test_user_create(self):
        self._asJaneDoe()
        new_user = {"username": "Test_User", "email": "Silly@silly.com", "password": "worms"}
        response = self._client.post("/users/", new_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(User.objects.filter(username="Test_User").exists(), False)
        self.assertEqual(User.objects.count(), 5)

    def test_admin_create(self):
        self._asAdmin()
        new_user = {"username": "Test_User",
                    "email": "Silly@silly.com",
                    "password": "worms",
                    "first_name": "Test",
                    "last_name": "User",
                    "groups": ["joe_group"]}
        response = self._client.post("/users/", new_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(User.objects.filter(username="Test_User").exists(), True)
        self.assertEqual(User.objects.count(), 6)
        user1 = User.objects.get(username="Test_User")
        self.assertEqual(user1.email, "Silly@silly.com")
        self.assertEqual(user1.first_name, "Test")
        self.assertEqual(user1.last_name, "User")
        self.assertEqual(user1.groups.count(), 2)
        self.assertEqual(set(user1.groups.all()),
                         set([Group.objects.get(name="user"), Group.objects.get(name="joe_group")]))

        # Other user still sees just theirs but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data
        self.assertEqual(len(users["results"]), 1)
        self._asAdmin()
        response = self._client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data
        self.assertEqual(len(users["results"]), 6)

    def test_user_edit_own(self):
        self._asJaneDoe()
        updated_user = {"email": "onion@apple.com"}
        response = self._client.patch("/users/%d/" % self._janeDoe.id,
                                      updated_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1 = User.objects.get(username="Jane Doe")
        self.assertEqual(user1.email, "onion@apple.com")

    def test_user_edit_other(self):
        # Others not permitted
        self._asJoeBloggs()
        updated_user = {"email": "onion@apple.com"}
        response = self._client.patch("/users/%d/" % self._janeDoe.id,
                                      updated_user, format='json')
        # Users cannot see other user so this is a 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        user1 = User.objects.get(username="Jane Doe")
        self.assertEqual(user1.email, "jane@tgac.com")

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_user = {"email": "onion@apple.com"}
        response = self._client.patch("/users/%d/" % self._janeDoe.id,
                                      updated_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1 = User.objects.get(username="Jane Doe")
        self.assertEqual(user1.email, "onion@apple.com")

    def test_user_change_own_password(self):
        self._asJaneDoe()
        new_password = {'new_password': 'super duper password'}
        response = self._client.post("/users/%d/change_password/" % self._janeDoe.id,
                                     new_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1 = User.objects.get(username="Jane Doe")
        self.assertIs(check_password('super duper password', user1.password), True)

    def test_user_change_other_password(self):
        self._asJoeBloggs()
        new_password = {'new_password': 'super duper password'}
        response = self._client.post("/users/%d/change_password/" % self._janeDoe.id,
                                     new_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user1 = User.objects.get(username="Joe Bloggs")
        self.assertIs(check_password('super duper password', user1.password), False)

    def test_admin_change_any_password(self):
        self._asAdmin()
        new_password = {'new_password': 'super duper password'}
        response = self._client.post("/users/%d/change_password/" % self._joeBloggs.id,
                                     new_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user1 = User.objects.get(username="Joe Bloggs")
        self.assertIs(check_password('super duper password', user1.password), True)

    def test_user_delete_own(self):
        self._asJoeBloggs()
        response = self._client.delete("/users/%d/" % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(User.objects.filter(username="Joe Bloggs").exists(), False)

    def test_user_delete_other(self):
        # Others not permitted
        self._asJaneDoe()
        response = self._client.delete("/users/%d/" % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(User.objects.filter(username="Joe Bloggs").exists(), True)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/users/%d/" % self._joeBloggs.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(User.objects.filter(username="Joe Bloggs").exists(), False)

    def test_anonymous_register(self):
        self._asAnonymous()
        new_user = {"username": "Test_User",
                    "email": "Silly@silly.com",
                    "password": "worms",
                    "first_name": "Test",
                    "last_name": "User",
                    "institution_name": "Unseen University",
                    "address_1": "1 Test Street",
                    "address_2": "Testwood",
                    "city": "Testington",
                    "postcode": "T1 1TS",
                    "country": "United Kingdom",
                    "groups": ["joe_group"]}
        response = self._client.post("/users/register/", new_user, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(User.objects.filter(username="Test_User").exists(), True)
        self.assertEqual(User.objects.count(), 6)
        user1 = User.objects.get(username="Test_User")
        self.assertEqual(user1.email, "Silly@silly.com")
        self.assertEqual(user1.first_name, "Test")
        self.assertEqual(user1.last_name, "User")
        self.assertIs(user1.groups.filter(name='user').exists(), True)
        self.assertEqual(user1.groups.count(), 2)
        self.assertEqual(set(user1.groups.all()),
                         set([Group.objects.get(name="user"), Group.objects.get(name="joe_group")]))

    def test_anonymous_invalid_list_staff(self):
        self._asAnonymous()
        response = self._client.get("/users/staff/", format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self._asInvalid()
        response = self._client.get("/users/staff/", format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_staff(self):
        self._asJoeBloggs()
        response = self._client.get("/users/staff/", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_admin_list_staff(self):
        self._asAdmin()
        response = self._client.get("/users/staff/", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The admin user is staff as well
        self.assertEqual(len(response.data), 2)


class GroupTestCase(LoggedInTestCase):
    def setUp(self):
        super(GroupTestCase, self).setUp()
        # No need to define any other groups as we have them from LoggedInTestCase already
        self._janeGroup = Group.objects.get(name="jane_group")
        self._joeGroup = Group.objects.get(name="joe_group")

    def test_presets(self):
        self.assertIs(Group.objects.filter(name="joe_group").exists(), True)
        self.assertIs(Group.objects.filter(name="jane_group").exists(), True)
        self.assertEqual(Group.objects.count(), 5)  # joe, jane, user, admin, staff
        self._joeGroup = Group.objects.get(name="joe_group")
        self._janeGroup = Group.objects.get(name="jane_group")

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/groups/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/groups/%d/' % self._joeGroup.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/groups/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/groups/%d/' % self._joeGroup.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        groups = response.data
        self.assertEqual(len(groups["results"]), 5)

    def test_user_view_any(self):
        self._asJoeBloggs()
        response = self._client.get('/groups/%d/' % self._janeGroup.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group1 = response.data
        self.assertEqual(group1["name"], "jane_group")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        groups = response.data
        self.assertEqual(len(groups["results"]), 5)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/groups/%d/' % self._janeGroup.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group1 = response.data
        self.assertEqual(group1["name"], "jane_group")

    def test_user_create(self):
        self._asJaneDoe()
        new_group = {"name": "Test_Group", "permissions": ["Can change equipment"]}
        response = self._client.post("/groups/", new_group, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Group.objects.filter(name="Test_Group").exists(), False)
        self.assertEqual(Group.objects.count(), 5)

    def test_admin_create(self):
        self._asAdmin()
        new_group = {"name": "Test_Group", "permissions": ["Can change equipment"]}
        response = self._client.post("/groups/", new_group, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(Group.objects.filter(name="Test_Group").exists(), True)
        self.assertEqual(Group.objects.count(), 6)
        group = Group.objects.get(name="Test_Group")
        self.assertEqual(set(group.permissions.all()),
                         set([Permission.objects.get(name="Can change equipment")]))

        # Other user sees the new one too
        self._asJoeBloggs()
        response = self._client.get('/groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        groups = response.data
        self.assertEqual(len(groups["results"]), 6)

    def test_user_edit_any(self):
        self._asJaneDoe()
        updated_group = {"permissions": ["Can change equipment"]}
        response = self._client.patch("/groups/%d/" % self._joeGroup.id,
                                      updated_group, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        group1 = Group.objects.get(name="joe_group")
        self.assertEqual(len(group1.permissions.all()), 0)

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_group = {"permissions": ["Can change equipment"]}
        response = self._client.patch("/groups/%d/" % self._joeGroup.id,
                                      updated_group, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group1 = Group.objects.get(name="joe_group")
        self.assertEqual(set(group1.permissions.all()),
                         set([Permission.objects.get(name="Can change equipment")]))

    def test_user_delete_any(self):
        self._asJoeBloggs()
        response = self._client.delete("/groups/%d/" % self._joeGroup.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Group.objects.filter(name="joe_group").exists(), True)

    def test_admin_delete_any(self):
        # Others not permitted
        self._asAdmin()
        response = self._client.delete("/groups/%d/" % self._joeGroup.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Group.objects.filter(name="joe_group").exists(), False)
