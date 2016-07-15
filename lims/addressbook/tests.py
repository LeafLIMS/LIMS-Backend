import json
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Address


class AddressTestCase(TestCase):
    def setUp(self):
        # These objects are recreated afresh for every test method below. Data updated or created in a test method
        # will not persist to another test method.
        self._client = APIClient()

        self._joeBloggs = User.objects.create_user(username='Joe Bloggs', email='joe@tgac.com', password='top_secret')
        self._janeDoe = User.objects.create_user(username='Jane Doe', email='jane@tgac.com', password='widget')

        self._joeBloggsAddress = \
            Address.objects.create(institution_name="Beetroot Institute", address_1="12 Muddy Field",
                                   address_2="Long Lane", city="Norwich", postcode="NR1 1AA", country="UK",
                                   user=self._joeBloggs)
        self._janeDoeAddress = \
            Address.objects.create(institution_name="Onion Institute", address_1="110a Deep Dark Wood",
                                   address_2="Bridge Street", city="Ipswich", postcode="IP1 1AA", country="UK",
                                   user=self._janeDoe)

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

    # Preset addresses from the constructor should return the values they were given
    def test_001_db_preset_addresses_correct(self):
        address1 = Address.objects.get(institution_name="Beetroot Institute")
        self.assertEqual(address1.institution_name, "Beetroot Institute")
        self.assertEqual(address1.address_1, "12 Muddy Field")
        self.assertEqual(address1.address_2, "Long Lane")
        self.assertEqual(address1.city, "Norwich")
        self.assertEqual(address1.postcode, "NR1 1AA")
        self.assertEqual(address1.country, "UK")
        self.assertEqual(address1.user, self._joeBloggs)
        self.assertEqual("%s" % address1, "Joe Bloggs: Beetroot Institute")
        address2 = Address.objects.get(institution_name="Onion Institute")
        self.assertEqual(address2.institution_name, "Onion Institute")
        self.assertEqual(address2.address_1, "110a Deep Dark Wood")
        self.assertEqual(address2.address_2, "Bridge Street")
        self.assertEqual(address2.city, "Ipswich")
        self.assertEqual(address2.postcode, "IP1 1AA")
        self.assertEqual(address2.country, "UK")
        self.assertEqual(address2.user, self._janeDoe)
        self.assertEqual("%s" % address2, "Jane Doe: Onion Institute")

    # Anonymous users or users with invalid credentials cannot see the address list or individual addresses
    def test_002a_rest_no_anonymous_or_invalid_access(self):
        self._asAnonymous()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self._asInvalid()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Users only see their own address(es) in the address list
    def test_003_rest_all_addresses_content(self):
        self._asJoeBloggs()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        addresses = response.data
        self.assertEqual(len(addresses["results"]), 1)
        address1 = addresses["results"][0]
        self.assertEqual(address1["institution_name"], "Beetroot Institute")
        self.assertEqual(address1["address_1"], "12 Muddy Field")
        self.assertEqual(address1["address_2"], "Long Lane")
        self.assertEqual(address1["city"], "Norwich")
        self.assertEqual(address1["postcode"], "NR1 1AA")
        self.assertEqual(address1["country"], "UK")

    # Users can see their own address when requested by address ID
    def test_004_rest_single_address_content(self):
        self._asJoeBloggs()
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        address1 = response.data
        self.assertEqual(address1["institution_name"], "Beetroot Institute")
        self.assertEqual(address1["address_1"], "12 Muddy Field")
        self.assertEqual(address1["address_2"], "Long Lane")
        self.assertEqual(address1["city"], "Norwich")
        self.assertEqual(address1["postcode"], "NR1 1AA")
        self.assertEqual(address1["country"], "UK")

    # Users cannot see addresses from other users when requested by address ID
    def test_005_rest_single_address_permissions(self):
        self._asJaneDoe()
        response = self._client.get('/addresses/%d/' % self._janeDoeAddress.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Users can add an extra address of their own
    def test_006_rest_create_address(self):
        # Create a new address of our own
        self._asJaneDoe()
        new_address = {"institution_name": "Leek Institute",
                       "address_1": "45 Mole Hill",
                       "address_2": "High St",
                       "city": "Cardiff",
                       "postcode": "CF1 1AA",
                       "country": "Wales",
                       "user": self._janeDoe.id}
        response = self._client.post("/addresses/", new_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # The DB now has 3 addresses in and that the new address is among them
        self.assertEqual(Address.objects.count(), 3)
        address = Address.objects.get(institution_name="Leek Institute")
        self.assertEqual(address.institution_name, "Leek Institute")
        self.assertEqual(address.address_1, "45 Mole Hill")
        self.assertEqual(address.address_2, "High St")
        self.assertEqual(address.city, "Cardiff")
        self.assertEqual(address.postcode, "CF1 1AA")
        self.assertEqual(address.country, "Wales")
        self.assertEqual(address.user, self._janeDoe)
        self.assertEqual("%s" % address, "Jane Doe: Leek Institute")

        # Other user still sees just their address but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        addresses = response.data
        self.assertEqual(len(addresses["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        addresses = response.data
        self.assertEqual(len(addresses["results"]), 2)

    # Should not be able to create an address for another user
    def test_007_rest_create_address_permissions(self):
        self._asJaneDoe()
        new_address = {"institution_name": "Jam Ltd.",
                       "address_1": "Sticky House",
                       "address_2": "Low St",
                       "city": "Hull",
                       "postcode": "H1 1AA",
                       "country": "UK",
                       "user": self._joeBloggs.id}
        response = self._client.post("/addresses/", new_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(Address.objects.filter(institution_name="Jam Ltd.").exists(), False)

    # Edit our own address and see the result reflected in the DB
    def test_008_rest_update_address(self):
        self._asJaneDoe()
        updated_address = {"institution_name": "Onion Institute Revised"}
        response = self._client.patch("/addresses/%d/" % self._janeDoeAddress.id, updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        address = Address.objects.get(institution_name="Onion Institute Revised")
        self.assertEqual(address.institution_name, "Onion Institute Revised")
        self.assertEqual(address.address_1, "110a Deep Dark Wood")
        self.assertEqual(address.address_2, "Bridge Street")
        self.assertEqual(address.city, "Ipswich")
        self.assertEqual(address.postcode, "IP1 1AA")
        self.assertEqual(address.country, "UK")
        self.assertEqual(address.user, self._janeDoe)
        self.assertEqual("%s" % address, "Jane Doe: Onion Institute Revised")

    # Should not be able to update the address of another user
    def test_009_rest_update_address_permissions(self):
        self._asJoeBloggs()
        updated_address = {"institution_name": "Toast Co."}
        response = self._client.put("/addresses/%d/" % self._janeDoeAddress.id, updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Address.objects.filter(institution_name="Onion Institute").exists(), True)
        self.assertIs(Address.objects.filter(institution_name="Toast Co.").exists(), False)

    # Delete own address
    def test_010_rest_delete_address(self):
        self._asJoeBloggs()
        response = self._client.delete("/addresses/%d/" % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Address.objects.filter(institution_name="Beetroot Institute").exists(), False)

    # Cannot delete someone else's address
    def test_011_rest_delete_address_permissions(self):
        self._asJaneDoe()
        response = self._client.delete("/addresses/%d/" % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Address.objects.filter(institution_name="Beetroot Institute").exists(), True)
