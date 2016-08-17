# import datetime
# from lims.shared.loggedintestcase import LoggedInTestCase
# from rest_framework import status
# from .models import Order, Service
#
#
# class OrderTestCase(LoggedInTestCase):
#     def setUp(self):
#         super(OrderTestCase, self).setUp()
#         # These objects are recreated afresh for every test method below.
#         # Data updated or created in a test method will not persist to another test method.
#         self._service_sequencing = Service.objects.create(name="Sequencing")
#         self._service_cleaning = Service.objects.create(name="Cleaning")
#         self._service_whistling = Service.objects.create(name="Whistling")
#
#         self._t_1 = datetime.datetime.now() - datetime.timedelta(days=6)
#         self._t_2 = datetime.datetime.now() - datetime.timedelta(days=5)
#         self._t_3 = datetime.datetime.now() - datetime.timedelta(days=4)
#         self._t_4 = datetime.datetime.now() - datetime.timedelta(days=3)
#         self._t_5 = datetime.datetime.now() - datetime.timedelta(days=2)
#         self._t_6 = datetime.datetime.now() - datetime.timedelta(days=1)
#
#         self._order1 = Order.objects.create(name="Order1",
#                                             status="In Limbo",
#                                             data={},
#                                             status_bar_status="Submitted",
#                                             user=self._joeBloggs,
#                                             date_placed=self._t_1,
#                                             date_updated=self._t_2,
#                                             is_quote=False,
#                                             quote_sent=False,
#                                             po_receieved=False,
#                                             po_reference=None,
#                                             invoice_sent=False,
#                                             has_paid=False)
#         self._order1.services.add(self._service_cleaning, self._service_sequencing)
#
#         self._order2 = Order.objects.create(name="Order2",
#                                             status="Done and dusted",
#                                             data={"Key1": "Value1", "Key2": "Value2"},
#                                             status_bar_status="Project Shipped",
#                                             user=self._janeDoe,
#                                             date_placed=self._t_3,
#                                             date_updated=self._t_4,
#                                             is_quote=True,
#                                             quote_sent=True,
#                                             po_receieved=True,
#                                             po_reference="PO1",
#                                             invoice_sent=True,
#                                             has_paid=True)
#         self._order2.services.add(self._service_whistling, self._service_sequencing)
#
#     # Preset orders from the constructor should return the values they were given
#     def test_001_db_preset_orders_correct(self):
#         self.assertIs(Order.objects.filter(name="Order1").exists(), True)
#         order1 = Order.objects.get(name="Order1")
#         self.assertEqual(order1.name, "Order1")
#         self.assertEqual(order1.status, "In Limbo")
#         self.assertEqual(order1.data, {})
#         self.assertEqual(order1.status_bar_status, "Submitted")
#         self.assertEqual(order1.user, self._joeBloggs)
#         self.assertEqual(order1.date_placed, self._t_1)
#         self.assertEqual(order1.date_updated, self._t_2)
#         self.assertIs(order1.is_quote, False)
#         self.assertIs(order1.quote_sent, False)
#         self.assertIs(order1.po_receieved, False)
#         self.assertIsNone(order1.po_reference)
#         self.assertIs(order1.invoice_sent, False)
#         self.assertIs(order1.has_paid, False)
#
#         self.assertIs(Order.objects.filter(name="Order2").exists(), True)
#         order2 = Order.objects.get(name="Order2")
#         self.assertEqual(order2.name, "Order2")
#         self.assertEqual(order2.status, "Done and dusted")
#         self.assertEqual(order2.data, {"Key1": "Value1", "Key2": "Value2"})
#         self.assertEqual(order2.status_bar_status, "Project Shipped")
#         self.assertEqual(order2.user, self._janeDoe)
#         self.assertEqual(order2.date_placed, self._t_3)
#         self.assertEqual(order2.date_updated, self._t_4)
#         self.assertIs(order2.is_quote, True)
#         self.assertIs(order2.quote_sent, True)
#         self.assertIs(order2.po_receieved, True)
#         self.assertEqual(order2.po_reference, "PO1")
#         self.assertIs(order2.invoice_sent, True)
#         self.assertIs(order2.has_paid, True)
#
#     # Anonymous users or users with invalid credentials
#     # cannot see the order list or individual orders
#     def test_002_rest_no_anonymous_or_invalid_access(self):
#         self._asAnonymous()
#         response = self._client.get('/orders/')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         response = self._client.get('/orders/%d/' % self._order1.id)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self._asInvalid()
#         response = self._client.get('/orders/')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         response = self._client.get('/orders/%d/' % self._order1.id)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#     # Users only see their own order(s) in the order list but staff can see all orders
#     def test_003_rest_all_orders_content(self):
#         self._asAdmin()
#         response = self._client.get('/orders/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         orders = response.data
#         self.assertEqual(len(orders["results"]), 2)
#         self._asJoeBloggs()
#         response = self._client.get('/orders/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         orders = response.data
#         self.assertEqual(len(orders["results"]), 1)
#         order1 = orders["results"][0]
#         self.assertEqual(order1["name"], "Order1")
#         self.assertEqual(order1["status"], "In Limbo")
#         self.assertEqual(order1["data"], {})
#         self.assertEqual(order1["status_bar_status"], "Submitted")
#         self.assertEqual(order1["date_placed"], self._t_1)
#         self.assertEqual(order1["date_updated"], self._t_2)
#         self.assertIs(order1["is_quote"], False)
#         self.assertIs(order1["quote_sent"], False)
#         self.assertIs(order1["po_receieved"], False)
#         self.assertIsNone(order1["po_reference"])
#         self.assertIs(order1["invoice_sent"], False)
#         self.assertIs(order1["has_paid"], False)
#
#     # Users can see their own order when requested by order ID
#     def test_004_rest_single_order_content(self):
#         self._asJoeBloggs()
#         response = self._client.get('/orders/%d/' % self._order1.id)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         order1 = response.data
#         self.assertEqual(order1["name"], "Order1")
#         self.assertEqual(order1["status"], "In Limbo")
#         self.assertEqual(order1["data"], {})
#         self.assertEqual(order1["status_bar_status"], "Submitted")
#         self.assertEqual(datetime.strptime(order1["date_placed"], "%Y-%m-%dT%H:%M:%S.%fZ"), self._t_1)
#         self.assertEqual(datetime.strptime(order1["date_updated"], "%Y-%m-%dT%H:%M:%S.%fZ"), self._t_2)
#         self.assertIs(order1["is_quote"], False)
#         self.assertIs(order1["quote_sent"], False)
#         self.assertIs(order1["po_receieved"], False)
#         self.assertIsNone(order1["po_reference"])
#         self.assertIs(order1["invoice_sent"], False)
#         self.assertIs(order1["has_paid"], False)
#
#     # Users cannot see orders from other users when requested by order ID
#     def test_005_rest_single_address_permissions(self):
#         self._asJaneDoe()
#         response = self._client.get('/orders/%d/' % self._order2.id)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         response = self._client.get('/orders/%d/' % self._order1.id)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#
#     # Users can add an order of their own
#     def test_006_rest_create_order(self):
#         # Create a new order of our own
#         self._asJaneDoe()
#         new_order = {"name": "Order3",
#                      "status": "YippyYah",
#                      "data": {},
#                      "status_bar_status": "Order Received",
#                      "date_placed": self._t_3,
#                      "date_updated": self._t_4,
#                      "is_quote": False,
#                      "quote_sent": False,
#                      "po_receieved": True,
#                      "po_reference": "PO2",
#                      "invoice_sent": True,
#                      "has_paid": False
#                      }
#         response = self._client.post("/orders/", new_order, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         # The DB now has 3 orders in and that the new order is among them
#         self.assertEqual(Order.objects.count(), 3)
#         self.assertIs(Order.objects.filter(name="Order3").exists(), True)
#         order3 = Order.objects.get(name="Order3")
#         self.assertEqual(order3.name, "Order3")
#         self.assertEqual(order3.status, "YippyYah")
#         self.assertEqual(order3.data, {})
#         self.assertEqual(order3.status_bar_status, "Order Received")
#         self.assertEqual(order3.user, self._janeDoe)
#         self.assertEqual(order3.date_placed, self._t_5)
#         self.assertEqual(order3.date_updated, self._t_6)
#         self.assertIs(order3.is_quote, False)
#         self.assertIs(order3.quote_sent, False)
#         self.assertIs(order3.po_receieved, True)
#         self.assertEqual(order3.po_reference, "PO2")
#         self.assertIs(order3.invoice_sent, True)
#         self.assertIs(order3.has_paid, False)
#
#         # Other user still sees just their order but we see both our old and new ones
#         self._asJoeBloggs()
#         response = self._client.get('/orders/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         orders = response.data
#         self.assertEqual(len(orders["results"]), 1)
#         self._asJaneDoe()
#         response = self._client.get('/orders/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         orders = response.data
#         self.assertEqual(len(orders["results"]), 2)
#
#     # Should not be able to create an order for another user
#     def test_007_rest_create_order_permissions(self):
#         self._asJaneDoe()
#         new_order = {"name": "Order4",
#                      "status": "YippyYah",
#                      "data": {},
#                      "status_bar_status": "Order Received",
#                      "user": self._joeBloggs.id,
#                      "date_placed": self._t_5,
#                      "date_updated": self._t_6,
#                      "is_quote": False,
#                      "quote_sent": False,
#                      "po_receieved": True,
#                      "po_reference": "PO2",
#                      "invoice_sent": True,
#                      "has_paid": False
#                      }
#         response = self._client.post("/orders/", new_order, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIs(Order.objects.filter(name="Order4").exists(), False)
#
#     # Edit our own order and see the result reflected in the DB
#     def test_008_rest_update_order(self):
#         self._asJaneDoe()
#         updated_address = {"name": "Order 5"}
#         response = self._client.patch("/orders/%d/" % self._order2.id,
#                                       updated_address, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         self.assertIs(Order.objects.filter(name="Order 5").exists(), True)
#         order5 = Order.objects.get(name="Order 5")
#         self.assertEqual(order5.name, "Order 5")
#         self.assertEqual(order5.status, "Done and dusted")
#         self.assertEqual(order5.data, {"Key1": "Value1", "Key2": "Value2"})
#         self.assertEqual(order5.status_bar_status, "Project Shipped")
#         self.assertEqual(order5.user, self._janeDoe)
#         self.assertEqual(order5.date_placed, self._t_3)
#         self.assertEqual(order5.date_updated, self._t_4)
#         self.assertIs(order5.is_quote, True)
#         self.assertIs(order5.quote_sent, True)
#         self.assertIs(order5.po_receieved, True)
#         self.assertEqual(order5.po_reference, "PO1")
#         self.assertIs(order5.invoice_sent, True)
#         self.assertIs(order5.has_paid, True)
#
#     # Should not be able to update the order of another user
#     def test_009_rest_update_order_permissions(self):
#         self._asJaneDoe()
#         updated_address = {"name": "Order 6"}
#         response = self._client.put("/orders/%d/" % self._order1.id,
#                                     updated_address, format='json')
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertIs(Order.objects.filter(name="Order1").exists(), True)
#         self.assertIs(Order.objects.filter(name="Order 6").exists(), False)
#
#     # Delete own order
#     def test_010_rest_delete_order(self):
#         self._asJoeBloggs()
#         response = self._client.delete("/orders/%d/" % self._order1.id)
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertIs(Order.objects.filter(name="Order1").exists(), False)
#
#     # Cannot delete someone else's order
#     def test_011_rest_delete_order_permissions(self):
#         self._asJoeBloggs()
#         response = self._client.delete("/orders/%d/" % self._order2.id)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertIs(Order.objects.filter(name="Order 2").exists(), True)
#
#         # TODO orders/autocomplete, orders/recent, orders/statuses
