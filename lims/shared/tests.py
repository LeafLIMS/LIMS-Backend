from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import Organism, Trigger, TriggerAlertStatus, TriggerAlert, TriggerSet, TriggerSubscription
from lims.addressbook.models import Address
from django.db.models.signals import post_save


class OrganismTestCase(LoggedInTestCase):
    def setUp(self):
        super(OrganismTestCase, self).setUp()

        self._human = \
            Organism.objects.create(name="Homo sapiens",
                                    common_name="Human")
        self._mouse = \
            Organism.objects.create(name="Mus musculus",
                                    common_name="Mouse")

    def test_presets(self):
        self.assertIs(Organism.objects.filter(name="Homo sapiens").exists(), True)
        organism1 = Organism.objects.get(name="Homo sapiens")
        self.assertEqual(organism1.common_name, "Human")
        self.assertIs(Organism.objects.filter(name="Mus musculus").exists(), True)
        organism2 = Organism.objects.get(name="Mus musculus")
        self.assertEqual(organism2.common_name, "Mouse")

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/organisms/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/organisms/%s/' % self._human.name)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/organisms/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/organisms/%s/' % self._human.name)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/organisms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        organisms = response.data
        self.assertEqual(len(organisms["results"]), 2)
        organism1 = organisms["results"][0]
        self.assertEqual(organism1["name"], "Homo sapiens")
        self.assertEqual(organism1["common_name"], "Human")

    def test_user_view(self):
        self._asJoeBloggs()
        response = self._client.get('/organisms/%d/' % self._mouse.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        organism1 = response.data
        self.assertEqual(organism1["name"], "Mus musculus")
        self.assertEqual(organism1["common_name"], "Mouse")

    def test_user_create(self):
        self._asJaneDoe()
        new_organism = {"name": "Bos taurus", "common_name": "Cow"}
        response = self._client.post("/organisms/", new_organism, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Organism.objects.count(), 2)
        self.assertIs(Organism.objects.filter(name="Bos taurus").exists(), False)

    def test_admin_create(self):
        self._asAdmin()
        new_organism = {"name": "Bos taurus", "common_name": "Cow"}
        response = self._client.post("/organisms/", new_organism, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organism.objects.count(), 3)
        self.assertIs(Organism.objects.filter(name="Bos taurus").exists(), True)
        organism1 = Organism.objects.get(name="Bos taurus")
        self.assertEqual(organism1.common_name, "Cow")

    def test_user_edit(self):
        self._asJoeBloggs()
        updated_organism = {"common_name": "Onion"}
        response = self._client.patch("/organisms/%d/" % self._mouse.id,
                                      updated_organism, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Organism.objects.filter(common_name="Mouse").exists(), True)
        self.assertIs(Organism.objects.filter(common_name="Onion").exists(), False)

    def test_admin_edit(self):
        self._asAdmin()
        updated_organism = {"common_name": "Onion"}
        response = self._client.patch("/organisms/%d/" % self._mouse.id,
                                      updated_organism, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Organism.objects.filter(common_name="Onion").exists(), True)
        organism1 = Organism.objects.get(common_name="Onion")
        self.assertEqual(organism1.name, "Mus musculus")

    def test_user_delete(self):
        self._asJaneDoe()
        response = self._client.delete("/organisms/%d/" % self._mouse.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Organism.objects.filter(name="Mus musculus").exists(), True)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete("/organisms/%d/" % self._mouse.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Organism.objects.filter(name="Mus musculus").exists(), False)

# TODO Add Trigger tests here


class TriggerTestCase(LoggedInTestCase):
    def setUp(self):
        super(TriggerTestCase, self).setUp()

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
        self._joeBloggsTriggerSet = \
            TriggerSet.objects.create(model="Address",
                                      severity=TriggerSet.LOW,
                                      name="Joe's Trigger")
        self._joeBloggsTrigger = \
            Trigger.objects.create(triggerSet=self._joeBloggsTriggerSet,
                                   field="city",
                                   operator=Trigger.EQ,
                                   value="London")
        self._joeBloggsTriggerSet.triggers.add(self._joeBloggsTrigger)
        self._joeBloggsSubscription = \
            TriggerSubscription.objects.create(triggerSet=self._joeBloggsTriggerSet,
                                               user=self._joeBloggs,
                                               email=False)
        self._janeDoeSubscription1 = \
            TriggerSubscription.objects.create(triggerSet=self._joeBloggsTriggerSet,
                                               user=self._janeDoe,
                                               email=False)

        self._janeDoeTriggerSet = \
            TriggerSet.objects.create(model="Address",
                                      severity=TriggerSet.MEDIUM,
                                      name="Jane's Trigger")
        self._janeDoeTrigger = \
            Trigger.objects.create(triggerSet=self._janeDoeTriggerSet,
                                   field="country",
                                   operator=Trigger.EQ,
                                   value="England")
        self._janeDoeTriggerSet.triggers.add(self._janeDoeTrigger)
        self._janeDoeSubscription2 = \
            TriggerSubscription.objects.create(triggerSet=self._janeDoeTriggerSet,
                                               user=self._janeDoe,
                                               email=False)

    def test_access_triggersets_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/triggersets/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/triggersets/%d/' % self._joeBloggsTriggerSet.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_triggersets_invalid(self):
        self._asInvalid()
        response = self._client.get('/triggersets/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/triggersets/%d/' % self._joeBloggsTriggerSet.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # TODO admin create trigger set
    # TODO user create trigger set - fail
    # TODO admin delete trigger set
    # TODO user delete trigger set - fail
    # TODO admin edit trigger set
    # TODO user edit trigger set - fail
    # TODO user view all trigger sets
    # TODO user view any trigger set
    # TODO user view triggers on trigger set
    # TODO user view subscriptions on trigger set

    def test_access_triggers_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/triggers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/triggers/%d/' % self._joeBloggsTrigger.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_triggers_invalid(self):
        self._asInvalid()
        response = self._client.get('/triggers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/triggers/%d/' % self._joeBloggsTrigger.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # TODO admin create trigger
    # TODO user create trigger - fail
    # TODO admin delete trigger
    # TODO user delete trigger - fail
    # TODO admin edit trigger
    # TODO user edit trigger - fail
    # TODO user view all triggers
    # TODO user view any trigger

    def test_access_subscriptions_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/subscriptions/%d/' % self._joeBloggsSubscription.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_subscriptions_invalid(self):
        self._asInvalid()
        response = self._client.get('/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/subscriptions/%d/' % self._joeBloggsSubscription.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # TODO admin create any subscription
    # TODO user create own subscription
    # TODO user create any subscription - fail
    # TODO admin edit any subscription
    # TODO user edit own subscription
    # TODO user edit any subscription - fail
    # TODO admin delete any subscription
    # TODO user delete own subscription
    # TODO user delete any subscription - fail
    # TODO admin view all subscriptions
    # TODO admin view any subscription
    # TODO user view all subscriptions - only own
    # TODO user view own subscription
    # TODO user view any subscription
    # TODO admin test email template call

    def test_access_alerts_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/alerts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/alerts/%d/' % 0)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_alerts_invalid(self):
        self._asInvalid()
        response = self._client.get('/alerts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/alerts/%d/' % 0)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _fire_alerts(self):
        # Re-enable signals to enable testing of them
        post_save.connect(receiver=TriggerSet._fire_trigger_sets, dispatch_uid='Fire Trigger Sets')
        self._asJaneDoe()
        updated_address = {"city": "London", "country": "England"}
        response = self._client.patch("/addresses/%d/" % self._janeDoeAddress.id,
                                      updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._asJoeBloggs()
        updated_address = {"country": "England"}
        response = self._client.patch("/addresses/%d/" % self._joeBloggsAddress.id,
                                      updated_address, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Disable signals to avoid affecting other tests
        post_save.disconnect(receiver=TriggerSet._fire_trigger_sets, dispatch_uid='Fire Trigger Sets')

    # TODO admin create alert - fail
    # TODO admin edit alert - fail
    # TODO admin delete alert - fail
    # TODO admin view all alerts
    # TODO admin view alert
    # TODO user create alert - fail
    # TODO user edit alert - fail
    # TODO user delete alert - fail

    def test_users_see_all_own_alerts(self):
        self._fire_alerts()
        self._asJaneDoe()
        response = self._client.get('/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerts = response.data["results"]
        self.assertEqual(len(alerts), 3)
        self._asJoeBloggs()
        response = self._client.get('/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerts = response.data["results"]
        self.assertEqual(len(alerts), 1)

    def test_joe_sees_own_alert(self):
        self._fire_alerts()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        self._asJoeBloggs()
        response = self._client.get('/alerts/%d/' % joe_alert_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert = response.data
        self.assertEqual(alert["triggerAlert"]["instanceId"], self._janeDoeAddress.id)

    def test_joe_sees_jane_alert(self):
        self._fire_alerts()
        jane_alert_id = self._janeDoeTriggerSet.alerts.all()[0].statuses.all()[0].id
        self._asJoeBloggs()
        response = self._client.get('/alerts/%d/' % jane_alert_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # TODO admin silence any alert
    # TODO user silence own alert
    # TODO user silence any alert - fail
    # TODO admin dismiss any alert
    # TODO user dismiss own alert
    # TODO user dismiss any alert -fail
