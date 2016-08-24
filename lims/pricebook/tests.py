from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import Price, PriceBook


class PriceBookTestCase(LoggedInTestCase):

    # TODO Re-enable DISABLED_ methods once SFDC works in testing mode (check for settings.TESTING)

    def setUp(self):
        super(PriceBookTestCase, self).setUp()

        self._price_pencil = Price.objects.create(name="Pencil", code="P1", identifier="PEN1", price=0.99)
        self._price_flask = Price.objects.create(name="Flask", code="F1", identifier="FLA1", price=4.47)
        self._price_widget = Price.objects.create(name="Widget", code="W1", identifier="WID1", price=15.60)

        self._pricebook1 = PriceBook.objects.create(name="PriceBook1",
                                                    description="Test 1",
                                                    identifier="PB1")
        self._pricebook1.prices.add(self._price_pencil, self._price_flask)

        self._pricebook2 = PriceBook.objects.create(name="PriceBook2",
                                                    description="Test 2",
                                                    identifier="PB2")
        self._pricebook2.prices.add(self._price_pencil, self._price_widget)

    def test_presets(self):
        # Check prices in first book
        self.assertIs(PriceBook.objects.filter(name="PriceBook1").exists(), True)
        pricebook1 = PriceBook.objects.get(name="PriceBook1")
        self.assertEqual(pricebook1.description, "Test 1")
        self.assertEqual(pricebook1.identifier, "PB1")
        prices1 = pricebook1.prices.all()
        self.assertEqual(len(prices1), 2)
        price1_1 = prices1[0]
        self.assertEqual(price1_1.name, "Pencil")
        self.assertEqual(price1_1.code, "P1")
        self.assertEqual(price1_1.identifier, "PEN1")
        self.assertEqual(price1_1.price, 0.99)
        price1_2 = prices1[1]
        self.assertEqual(price1_2.name, "Flask")
        self.assertEqual(price1_2.code, "F1")
        self.assertEqual(price1_2.identifier, "FLA1")
        self.assertEqual(price1_2.price, 4.47)
        # Check prices in second book
        self.assertIs(PriceBook.objects.filter(name="PriceBook2").exists(), True)
        pricebook2 = PriceBook.objects.get(name="PriceBook2")
        self.assertEqual(pricebook2.description, "Test 2")
        self.assertEqual(pricebook2.identifier, "PB2")
        prices2 = pricebook2.prices.all()
        self.assertEqual(len(prices2), 2)
        price2_1 = prices2[0]
        self.assertEqual(price2_1.name, "Pencil")
        self.assertEqual(price2_1.code, "P1")
        self.assertEqual(price2_1.identifier, "PEN1")
        self.assertEqual(price2_1.price, 0.99)
        price2_2 = prices2[1]
        self.assertEqual(price2_2.name, "Widget")
        self.assertEqual(price2_2.code, "W1")
        self.assertEqual(price2_2.identifier, "WID1")
        self.assertEqual(price2_2.price, 15.60)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/pricebooks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/pricebooks/%d/' % self._pricebook1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/pricebooks/updateall/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/pricebooks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/pricebooks/%d/' % self._pricebook1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/pricebooks/updateall/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/pricebooks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pricebooks = response.data
        self.assertEqual(len(pricebooks["results"]), 2)

    def test_user_view(self):
        self._asJaneDoe()
        response = self._client.get('/pricebooks/%d/' % self._pricebook1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pricebook1 = response.data
        self.assertEqual(pricebook1["name"], "PriceBook1")
        self.assertEqual(pricebook1["description"], "Test 1")
        self.assertEqual(pricebook1["identifier"], "PB1")
        prices1 = pricebook1["prices"]
        self.assertEqual(len(prices1), 2)
        price1_1 = prices1[0]
        self.assertEqual(price1_1["name"], "Pencil")
        self.assertEqual(price1_1["code"], "P1")
        self.assertEqual(price1_1["identifier"], "PEN1")
        self.assertEqual(price1_1["price"], 0.99)
        price1_2 = prices1[1]
        self.assertEqual(price1_2["name"], "Flask")
        self.assertEqual(price1_2["code"], "F1")
        self.assertEqual(price1_2["identifier"], "FLA1")
        self.assertEqual(price1_2["price"], 4.47)

    def test_user_create(self):
        self._asJaneDoe()
        new_pricebook1 = {"name": "Test Pricebook",
                          "description": "What a lot of fun this is",
                          "identifier": "TP1",
                          "prices": [self._price_flask.id, self._price_widget.id]
                          }
        response = self._client.post("/pricebooks/", new_pricebook1, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PriceBook.objects.count(), 2)

    def test_admin_create(self):
        self._asAdmin()
        new_pricebook1 = {"name": "Test Pricebook",
                          "description": "What a lot of fun this is",
                          "identifier": "TP1",
                          "prices": [self._price_flask.id, self._price_widget.id]
                          }
        response = self._client.post("/pricebooks/", new_pricebook1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PriceBook.objects.count(), 3)
        self.assertIs(PriceBook.objects.filter(name="Test Pricebook").exists(), True)

    def test_user_edit(self):
        self._asJoeBloggs()
        updated_pricebook = {"description": "Hey ho"}
        response = self._client.patch("/pricebooks/%d/" % self._pricebook1.id,
                                      updated_pricebook, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(PriceBook.objects.filter(description="Test 1").exists(), True)
        self.assertIs(PriceBook.objects.filter(description="Hey ho").exists(), False)

    def test_admin_edit(self):
        self._asAdmin()
        updated_pricebook = {"description": "Hey ho"}
        response = self._client.patch("/pricebooks/%d/" % self._pricebook1.id,
                                      updated_pricebook, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(PriceBook.objects.filter(description="Test 1").exists(), False)
        self.assertIs(PriceBook.objects.filter(description="Hey ho").exists(), True)

    def test_user_delete(self):
        self._asJoeBloggs()
        response = self._client.delete("/pricebooks/%d/" % self._pricebook1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(PriceBook.objects.filter(description="Test 1").exists(), True)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete("/pricebooks/%d/" % self._pricebook1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(PriceBook.objects.filter(description="Test 1").exists(), False)

    def DISABLED_test_user_updateall(self):
        self._asJoeBloggs()
        response = self._client.get("/pricebooks/updateall/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Pricebooks updated")

    def DISABLED_test_admin_updateall(self):
        self._asAdmin()
        response = self._client.get("/pricebooks/updateall/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Pricebooks updated")
