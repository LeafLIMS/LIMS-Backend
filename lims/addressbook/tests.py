from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import Address


class AddressTestCase(LoggedInTestCase):

    def setUp(self):
        super(AddressTestCase, self).setUp()

        self._joeBloggsAddress = \
            Address.objects.create(institution_name="Beetroot Institute",
                                   address_1="12 Muddy Field",
                                   address_2="Long Lane",
                                   city="Norwich",
                                   postcode="NR1 1AA",
                                   country="UK",
                                   user=self._joeBloggs)
        self._janeDoeAddress = \
            Address.objects.create(institution_name="Onion Institute",
                                   address_1="110a Deep Dark Wood",
                                   address_2="Bridge Street",
                                   city="Ipswich",
                                   postcode="IP1 1AA",
                                   country="UK",
                                   user=self._janeDoe)

    def test_presets(self):
        self.assertIs(Address.objects.filter(institution_name="Beetroot Institute").exists(), True)
        address1 = Address.objects.get(institution_name="Beetroot Institute")
        self.assertEqual(address1.institution_name, "Beetroot Institute")
        self.assertEqual(address1.address_1, "12 Muddy Field")
        self.assertEqual(address1.address_2, "Long Lane")
        self.assertEqual(address1.city, "Norwich")
        self.assertEqual(address1.postcode, "NR1 1AA")
        self.assertEqual(address1.country, "UK")
        self.assertEqual(address1.user, self._joeBloggs)
        self.assertIs(Address.objects.filter(institution_name="Onion Institute").exists(), True)
        address2 = Address.objects.get(institution_name="Onion Institute")
        self.assertEqual(address2.institution_name, "Onion Institute")
        self.assertEqual(address2.address_1, "110a Deep Dark Wood")
        self.assertEqual(address2.address_2, "Bridge Street")
        self.assertEqual(address2.city, "Ipswich")
        self.assertEqual(address2.postcode, "IP1 1AA")
        self.assertEqual(address2.country, "UK")
        self.assertEqual(address2.user, self._janeDoe)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Others not permitted
        self._asJoeBloggs()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        addresses = response.data
        self.assertEqual(len(addresses["results"]), 1)
        address1 = addresses["results"][0]
        self.assertEqual(address1["institution_name"], "Beetroot Institute")

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        address1 = response.data
        self.assertEqual(address1["institution_name"], "Beetroot Institute")

    def test_user_view_other(self):
        # Others not permitted
        self._asJaneDoe()
        response = self._client.get('/addresses/%d/' % self._janeDoeAddress.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        addresses = response.data
        self.assertEqual(len(addresses["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/addresses/%d/' % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        address1 = response.data
        self.assertEqual(address1["institution_name"], "Beetroot Institute")

    def test_user_create_own(self):
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

        self.assertEqual(Address.objects.count(), 3)
        self.assertIs(Address.objects.filter(institution_name="Leek Institute").exists(), True)
        address = Address.objects.get(institution_name="Leek Institute")
        self.assertEqual(address.institution_name, "Leek Institute")
        self.assertEqual(address.address_1, "45 Mole Hill")
        self.assertEqual(address.address_2, "High St")
        self.assertEqual(address.city, "Cardiff")
        self.assertEqual(address.postcode, "CF1 1AA")
        self.assertEqual(address.country, "Wales")
        self.assertEqual(address.user, self._janeDoe)

        # Other user still sees just theirs but we see both our old and new ones
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

    def test_user_create_other(self):
        # Others not permitted
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

    def test_admin_create_any(self):
        self._asAdmin()
        new_address = {"institution_name": "Leek Institute",
                       "address_1": "45 Mole Hill",
                       "address_2": "High St",
                       "city": "Cardiff",
                       "postcode": "CF1 1AA",
                       "country": "Wales",
                       "user": self._janeDoe.id}
        response = self._client.post("/addresses/", new_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Address.objects.count(), 3)
        self.assertIs(Address.objects.filter(institution_name="Leek Institute").exists(), True)
        address = Address.objects.get(institution_name="Leek Institute")
        self.assertEqual(address.institution_name, "Leek Institute")
        self.assertEqual(address.address_1, "45 Mole Hill")
        self.assertEqual(address.address_2, "High St")
        self.assertEqual(address.city, "Cardiff")
        self.assertEqual(address.postcode, "CF1 1AA")
        self.assertEqual(address.country, "Wales")
        self.assertEqual(address.user, self._janeDoe)

        # Other user still sees just theirs but we see both our old and new ones
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

    def test_user_edit_own(self):
        self._asJaneDoe()
        updated_address = {"institution_name": "Onion Institute Revised"}
        response = self._client.patch("/addresses/%d/" % self._janeDoeAddress.id,
                                      updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(Address.objects.filter(institution_name="Onion Institute Revised").exists(),
                      True)
        address = Address.objects.get(institution_name="Onion Institute Revised")
        self.assertEqual(address.institution_name, "Onion Institute Revised")
        self.assertEqual(address.address_1, "110a Deep Dark Wood")
        self.assertEqual(address.address_2, "Bridge Street")
        self.assertEqual(address.city, "Ipswich")
        self.assertEqual(address.postcode, "IP1 1AA")
        self.assertEqual(address.country, "UK")
        self.assertEqual(address.user, self._janeDoe)

    def test_user_edit_other(self):
        # Others not permitted
        self._asJoeBloggs()
        updated_address = {"institution_name": "Toast Co."}
        response = self._client.put("/addresses/%d/" % self._janeDoeAddress.id,
                                    updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Address.objects.filter(institution_name="Onion Institute").exists(), True)
        self.assertIs(Address.objects.filter(institution_name="Toast Co.").exists(), False)

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_address = {"institution_name": "Onion Institute Revised"}
        response = self._client.patch("/addresses/%d/" % self._janeDoeAddress.id,
                                      updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(Address.objects.filter(institution_name="Onion Institute Revised").exists(),
                      True)
        address = Address.objects.get(institution_name="Onion Institute Revised")
        self.assertEqual(address.institution_name, "Onion Institute Revised")
        self.assertEqual(address.address_1, "110a Deep Dark Wood")
        self.assertEqual(address.address_2, "Bridge Street")
        self.assertEqual(address.city, "Ipswich")
        self.assertEqual(address.postcode, "IP1 1AA")
        self.assertEqual(address.country, "UK")
        self.assertEqual(address.user, self._janeDoe)

    def test_user_delete_own(self):
        self._asJoeBloggs()
        response = self._client.delete("/addresses/%d/" % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Address.objects.filter(institution_name="Beetroot Institute").exists(), False)

    def test_user_delete_other(self):
        # Others not permitted
        self._asJaneDoe()
        response = self._client.delete("/addresses/%d/" % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Address.objects.filter(institution_name="Beetroot Institute").exists(), True)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/addresses/%d/" % self._joeBloggsAddress.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Address.objects.filter(institution_name="Beetroot Institute").exists(), False)
