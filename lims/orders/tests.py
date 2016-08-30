from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import Order, Service


class OrderTestCase(LoggedInTestCase):
    # TODO Re-enable DISABLED_ methods once SFDC works in testing mode (check for settings.TESTING)
    # TODO Implement SFDC tests once SFDC works in testing mode (check for settings.TESTING)

    def setUp(self):
        super(OrderTestCase, self).setUp()

        self._service_sequencing = Service.objects.create(name="Sequencing")
        self._service_cleaning = Service.objects.create(name="Cleaning")
        self._service_whistling = Service.objects.create(name="Whistling")

        self._order1 = Order.objects.create(name="Order1",
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
        self._order1.services.add(self._service_cleaning, self._service_sequencing)

        self._order2 = Order.objects.create(name="Order2",
                                            status="Done and dusted",
                                            data={"Key1": "Value1", "Key2": "Value2"},
                                            status_bar_status="Project Shipped",
                                            user=self._janeDoe,
                                            is_quote=True,
                                            quote_sent=True,
                                            po_receieved=True,
                                            po_reference="PO1",
                                            invoice_sent=True,
                                            has_paid=True)
        self._order2.services.add(self._service_whistling, self._service_sequencing)

    def test_presets(self):
        self.assertIs(Order.objects.filter(name="Order1").exists(), True)
        order1 = Order.objects.get(name="Order1")
        self.assertEqual(order1.name, "Order1")
        self.assertEqual(order1.status, "In Limbo")
        self.assertEqual(order1.data, {})
        self.assertEqual(order1.status_bar_status, "Submitted")
        self.assertEqual(order1.user, self._joeBloggs)
        self.assertIs(order1.is_quote, False)
        self.assertIs(order1.quote_sent, False)
        self.assertIs(order1.po_receieved, False)
        self.assertIsNone(order1.po_reference)
        self.assertIs(order1.invoice_sent, False)
        self.assertIs(order1.has_paid, False)

        self.assertIs(Order.objects.filter(name="Order2").exists(), True)
        order2 = Order.objects.get(name="Order2")
        self.assertEqual(order2.name, "Order2")
        self.assertEqual(order2.status, "Done and dusted")
        self.assertEqual(order2.data, {"Key1": "Value1", "Key2": "Value2"})
        self.assertEqual(order2.status_bar_status, "Project Shipped")
        self.assertEqual(order2.user, self._janeDoe)
        self.assertIs(order2.is_quote, True)
        self.assertIs(order2.quote_sent, True)
        self.assertIs(order2.po_receieved, True)
        self.assertEqual(order2.po_reference, "PO1")
        self.assertIs(order2.invoice_sent, True)
        self.assertIs(order2.has_paid, True)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/orders/statuses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/orders/recent/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        query4 = {"q": "flibble"}
        response = self._client.get("/orders/autocomplete/", query4, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/orders/%d/' % self._order1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/orders/statuses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/orders/recent/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        query4 = {"q": "flibble"}
        response = self._client.get("/orders/autocomplete/", query4, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/orders/%d/' % self._order1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders = response.data
        self.assertEqual(len(orders["results"]), 1)
        order1 = orders["results"][0]
        self.assertEqual(order1["name"], "Order1")
        self.assertEqual(order1["status"], "In Limbo")
        self.assertEqual(order1["data"], {})
        self.assertEqual(order1["status_bar_status"], "Submitted")
        self.assertIs(order1["is_quote"], False)
        self.assertIs(order1["quote_sent"], False)
        self.assertIs(order1["po_receieved"], False)
        self.assertIsNone(order1["po_reference"])
        self.assertIs(order1["invoice_sent"], False)
        self.assertIs(order1["has_paid"], False)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/orders/%d/' % self._order1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order1 = response.data
        self.assertEqual(order1["name"], "Order1")
        self.assertEqual(order1["status"], "In Limbo")
        self.assertEqual(order1["data"], {})
        self.assertEqual(order1["status_bar_status"], "Submitted")
        self.assertIs(order1["is_quote"], False)
        self.assertIs(order1["quote_sent"], False)
        self.assertIs(order1["po_receieved"], False)
        self.assertIsNone(order1["po_reference"])
        self.assertIs(order1["invoice_sent"], False)
        self.assertIs(order1["has_paid"], False)

    def test_user_view_other(self):
        self._asJaneDoe()
        response = self._client.get('/orders/%d/' % self._order2.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._client.get('/orders/%d/' % self._order1.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders = response.data
        self.assertEqual(len(orders["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/orders/%d/' % self._order1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order1 = response.data
        self.assertEqual(order1["name"], "Order1")
        self.assertEqual(order1["status"], "In Limbo")
        self.assertEqual(order1["data"], {})
        self.assertEqual(order1["status_bar_status"], "Submitted")
        self.assertIs(order1["is_quote"], False)
        self.assertIs(order1["quote_sent"], False)
        self.assertIs(order1["po_receieved"], False)
        self.assertIsNone(order1["po_reference"])
        self.assertIs(order1["invoice_sent"], False)
        self.assertIs(order1["has_paid"], False)

    def DISABLED_test_user_create_own(self):
        self._asJaneDoe()
        new_order = {"name": "Order3",
                     "status": "YippyYah",
                     "data": {},
                     "status_bar_status": "Order Received",
                     "is_quote": False,
                     "quote_sent": False,
                     "po_receieved": True,
                     "po_reference": "PO2",
                     "invoice_sent": True,
                     "has_paid": False
                     }
        response = self._client.post("/orders/", new_order, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # The DB now has 3 orders in and that the new order is among them
        self.assertEqual(Order.objects.count(), 3)
        self.assertIs(Order.objects.filter(name="Order3").exists(), True)
        order3 = Order.objects.get(name="Order3")
        self.assertEqual(order3.name, "Order3")
        self.assertEqual(order3.status, "YippyYah")
        self.assertEqual(order3.data, {})
        self.assertEqual(order3.status_bar_status, "Order Received")
        self.assertEqual(order3.user, self._janeDoe)
        self.assertIs(order3.is_quote, False)
        self.assertIs(order3.quote_sent, False)
        self.assertIs(order3.po_receieved, True)
        self.assertEqual(order3.po_reference, "PO2")
        self.assertIs(order3.invoice_sent, True)
        self.assertIs(order3.has_paid, False)

        # Other user still sees just their order but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders = response.data
        self.assertEqual(len(orders["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders = response.data
        self.assertEqual(len(orders["results"]), 2)

    def DISABLED_test_user_create_other(self):
        self._asJaneDoe()
        new_order = {"name": "Order4",
                     "status": "YippyYah",
                     "data": {},
                     "status_bar_status": "Order Received",
                     "user": self._joeBloggs.id,
                     "is_quote": False,
                     "quote_sent": False,
                     "po_receieved": True,
                     "po_reference": "PO2",
                     "invoice_sent": True,
                     "has_paid": False
                     }
        response = self._client.post("/orders/", new_order, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(Order.objects.filter(name="Order4").exists(), False)

    def DISABLED_test_admin_create_any(self):
        self._asAdmin()
        new_order = {"name": "Order3",
                     "status": "YippyYah",
                     "data": {},
                     "status_bar_status": "Order Received",
                     "is_quote": False,
                     "quote_sent": False,
                     "po_receieved": True,
                     "po_reference": "PO2",
                     "invoice_sent": True,
                     "has_paid": False
                     }
        response = self._client.post("/orders/", new_order, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # The DB now has 3 orders in and that the new order is among them
        self.assertEqual(Order.objects.count(), 3)
        self.assertIs(Order.objects.filter(name="Order3").exists(), True)
        order3 = Order.objects.get(name="Order3")
        self.assertEqual(order3.name, "Order3")
        self.assertEqual(order3.status, "YippyYah")
        self.assertEqual(order3.data, {})
        self.assertEqual(order3.status_bar_status, "Order Received")
        self.assertEqual(order3.user, self._janeDoe)
        self.assertIs(order3.is_quote, False)
        self.assertIs(order3.quote_sent, False)
        self.assertIs(order3.po_receieved, True)
        self.assertEqual(order3.po_reference, "PO2")
        self.assertIs(order3.invoice_sent, True)
        self.assertIs(order3.has_paid, False)

        # Other user still sees just their order but we see both our old and new ones
        self._asJoeBloggs()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders = response.data
        self.assertEqual(len(orders["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders = response.data
        self.assertEqual(len(orders["results"]), 2)

    def test_user_edit_own(self):
        self._asJaneDoe()
        updated_address = {"name": "Order 5"}
        response = self._client.patch("/orders/%d/" % self._order2.id,
                                      updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(Order.objects.filter(name="Order 5").exists(), True)
        order5 = Order.objects.get(name="Order 5")
        self.assertEqual(order5.name, "Order 5")
        self.assertEqual(order5.status, "Done and dusted")
        self.assertEqual(order5.data, {"Key1": "Value1", "Key2": "Value2"})
        self.assertEqual(order5.status_bar_status, "Project Shipped")
        self.assertEqual(order5.user, self._janeDoe)
        self.assertIs(order5.is_quote, True)
        self.assertIs(order5.quote_sent, True)
        self.assertIs(order5.po_receieved, True)
        self.assertEqual(order5.po_reference, "PO1")
        self.assertIs(order5.invoice_sent, True)
        self.assertIs(order5.has_paid, True)

    def test_user_edit_other(self):
        self._asJaneDoe()
        updated_address = {"name": "Order 6"}
        response = self._client.put("/orders/%d/" % self._order1.id,
                                    updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Order.objects.filter(name="Order1").exists(), True)
        self.assertIs(Order.objects.filter(name="Order 6").exists(), False)

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_address = {"name": "Order 5"}
        response = self._client.patch("/orders/%d/" % self._order2.id,
                                      updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIs(Order.objects.filter(name="Order 5").exists(), True)
        order5 = Order.objects.get(name="Order 5")
        self.assertEqual(order5.name, "Order 5")
        self.assertEqual(order5.status, "Done and dusted")
        self.assertEqual(order5.data, {"Key1": "Value1", "Key2": "Value2"})
        self.assertEqual(order5.status_bar_status, "Project Shipped")
        self.assertEqual(order5.user, self._janeDoe)
        self.assertIs(order5.is_quote, True)
        self.assertIs(order5.quote_sent, True)
        self.assertIs(order5.po_receieved, True)
        self.assertEqual(order5.po_reference, "PO1")
        self.assertIs(order5.invoice_sent, True)
        self.assertIs(order5.has_paid, True)

    def test_user_delete_own(self):
        self._asJoeBloggs()
        response = self._client.delete("/orders/%d/" % self._order1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Order.objects.filter(name="Order1").exists(), False)

    def test_user_delete_other(self):
        self._asJoeBloggs()
        response = self._client.delete("/orders/%d/" % self._order2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Order.objects.filter(name="Order2").exists(), True)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/orders/%d/" % self._order1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Order.objects.filter(name="Order1").exists(), False)

    def test_autocomplete_match_only_user1(self):
        query1 = {"q": "er1"}
        self._asJoeBloggs()
        response = self._client.get("/orders/autocomplete/", query1, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self._order1.id)
        self._asJaneDoe()
        response = self._client.get("/orders/autocomplete/", query1, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self._asAdmin()
        response = self._client.get("/orders/autocomplete/", query1, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self._order1.id)

    def test_autocomplete_match_only_user2(self):
        query2 = {"q": "er2"}
        self._asJoeBloggs()
        response = self._client.get("/orders/autocomplete/", query2, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self._asJaneDoe()
        response = self._client.get("/orders/autocomplete/", query2, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self._order2.id)
        self._asAdmin()
        response = self._client.get("/orders/autocomplete/", query2, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self._order2.id)

    def test_autocomplete_match_both_users(self):
        query3 = {"q": "rde"}
        self._asJoeBloggs()
        response = self._client.get("/orders/autocomplete/", query3, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self._order1.id)
        self._asJaneDoe()
        response = self._client.get("/orders/autocomplete/", query3, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self._order2.id)
        self._asAdmin()
        response = self._client.get("/orders/autocomplete/", query3, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], self._order2.id)  # Most recent first
        self.assertEqual(response.data[1]["id"], self._order1.id)

    def test_autocomplete_no_match(self):
        query4 = {"q": "flibble"}
        self._asJoeBloggs()
        response = self._client.get("/orders/autocomplete/", query4, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self._asJaneDoe()
        response = self._client.get("/orders/autocomplete/", query4, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self._asAdmin()
        response = self._client.get("/orders/autocomplete/", query4, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_recent_orders(self):
        self._asJoeBloggs()
        response = self._client.get("/orders/recent/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recent = response.data
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["id"], self._order1.id)
        self._asAdmin()
        response = self._client.get("/orders/recent/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recent = response.data
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["id"], self._order2.id)  # Most recent first
        self.assertEqual(recent[1]["id"], self._order1.id)

    def test_status_list(self):
        self._asJoeBloggs()
        response = self._client.get("/orders/statuses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        statuses = response.data
        self.assertEqual(len(statuses), 5)
        self.assertEqual(statuses,
                         ["Submitted", "Quote Sent", "Order Received", "Project in Progress",
                          "Project Shipped"])
