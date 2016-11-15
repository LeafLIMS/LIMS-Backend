from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import Organism, Trigger, TriggerAlertStatus, TriggerAlert, TriggerSet, \
    TriggerSubscription
from lims.addressbook.models import Address
from django.db.models.signals import post_save
import datetime


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
            Trigger.objects.create(triggerset=self._joeBloggsTriggerSet,
                                   field="city",
                                   operator=Trigger.EQ,
                                   value="London")
        self._joeBloggsTriggerSet.triggers.add(self._joeBloggsTrigger)
        self._joeBloggsSubscription = \
            TriggerSubscription.objects.create(triggerset=self._joeBloggsTriggerSet,
                                               user=self._joeBloggs,
                                               email=False)
        self._janeDoeSubscription1 = \
            TriggerSubscription.objects.create(triggerset=self._joeBloggsTriggerSet,
                                               user=self._janeDoe,
                                               email=False)

        self._janeDoeTriggerSet = \
            TriggerSet.objects.create(model="Address",
                                      severity=TriggerSet.MEDIUM,
                                      name="Jane's Trigger")
        self._janeDoeTrigger = \
            Trigger.objects.create(triggerset=self._janeDoeTriggerSet,
                                   field="country",
                                   operator=Trigger.EQ,
                                   value="England")
        self._janeDoeTriggerSet.triggers.add(self._janeDoeTrigger)
        self._janeDoeSubscription2 = \
            TriggerSubscription.objects.create(triggerset=self._janeDoeTriggerSet,
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

    def test_admin_create_triggerset(self):
        self._asAdmin()
        new_set = {"model": "Address",
                   "severity": TriggerSet.MEDIUM,
                   "name": "Jim's Trigger"}
        response = self._client.post("/triggersets/", new_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TriggerSet.objects.count(), 3)
        self.assertEqual(TriggerSet.objects.filter(name="Jim's Trigger").count(), 1)

    def test_user_create_triggerset(self):
        self._asJaneDoe()
        new_set = {"model": "Address",
                   "severity": TriggerSet.MEDIUM,
                   "name": "Jim's Trigger"}
        response = self._client.post("/triggersets/", new_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TriggerSet.objects.count(), 2)

    def test_admin_delete_triggerset(self):
        self._asAdmin()
        set_id = self._joeBloggsTriggerSet.id
        response = self._client.delete("/triggersets/%d/" % set_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(TriggerSet.objects.filter(id=set_id).exists(), False)

    def test_user_delete_triggerset(self):
        self._asJoeBloggs()
        set_id = self._joeBloggsTriggerSet.id
        response = self._client.delete("/triggersets/%d/" % set_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(TriggerSet.objects.filter(id=set_id).exists(), True)

    def test_admin_edit_triggerset(self):
        self._asAdmin()
        set_id = self._joeBloggsTriggerSet.id
        updated_alert = {"severity": TriggerSet.HIGH}
        response = self._client.patch("/triggersets/%d/" % set_id,
                                      updated_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TriggerSet.objects.filter(severity=TriggerSet.HIGH).count(), 1)
        self.assertEqual(TriggerSet.objects.get(id=set_id).severity, TriggerSet.HIGH)

    def test_user_edit_triggerset(self):
        self._asJaneDoe()
        set_id = self._joeBloggsTriggerSet.id
        updated_alert = {"severity": TriggerSet.HIGH}
        response = self._client.patch("/triggersets/%d/" % set_id,
                                      updated_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TriggerSet.objects.filter(severity=TriggerSet.HIGH).count(), 0)

    def test_user_sees_all_triggersets(self):
        self._asJaneDoe()
        response = self._client.get('/triggersets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        triggersets = response.data["results"]
        self.assertEqual(len(triggersets), 2)

    def test_user_sees_any_triggerset(self):
        self._asJaneDoe()
        set_id = self._joeBloggsTriggerSet.id
        response = self._client.get('/triggersets/%d/' % set_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ts = response.data
        self.assertEqual(ts["id"], self._joeBloggsTriggerSet.id)
        self.assertEqual(ts["severity"], TriggerSet.LOW)

    def test_user_sees_any_triggerset_triggers(self):
        self._asJaneDoe()
        set_id = self._joeBloggsTriggerSet.id
        response = self._client.get('/triggersets/%d/triggers/' % set_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ts = response.data
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0]["id"], self._joeBloggsTrigger.id)

    def test_user_sees_any_triggerset_subscriptions(self):
        self._asJaneDoe()
        set_id = self._joeBloggsTriggerSet.id
        response = self._client.get('/triggersets/%d/subscriptions/' % set_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ss = response.data
        self.assertEqual(len(ss), 2)
        self.assertEqual(set([ss[0]["id"], ss[1]["id"]]), set(
            [self._joeBloggsSubscription.id, self._janeDoeSubscription1.id]))

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

    def test_admin_create_trigger(self):
        self._asAdmin()
        new_trig = {"triggerset_id": self._joeBloggsTriggerSet.id,
                    "field": "postcode",
                    "operator": Trigger.EQ,
                    "value": "W1A 1AA",
                    "fire_on_create": False
                    }
        response = self._client.post("/triggers/", new_trig, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Trigger.objects.count(), 3)
        self.assertEqual(Trigger.objects.filter(triggerset=self._joeBloggsTriggerSet).count(), 2)

    def test_user_create_trigger(self):
        self._asJaneDoe()
        new_trig = {"triggerset_id": self._joeBloggsTriggerSet.id,
                    "field": "postcode",
                    "operator": Trigger.EQ,
                    "value": "W1A 1AA",
                    "fire_on_create": False
                    }
        response = self._client.post("/triggers/", new_trig, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_edit_trigger(self):
        self._asAdmin()
        trig_id = self._joeBloggsTrigger.id
        updated_trig = {"value": "W1A 1AA"}
        response = self._client.patch("/triggers/%d/" % trig_id,
                                      updated_trig, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Trigger.objects.filter(value="W1A 1AA").count(), 1)
        self.assertEqual(Trigger.objects.get(id=trig_id).value, "W1A 1AA")

    def test_user_edit_trigger(self):
        self._asJoeBloggs()
        trig_id = self._joeBloggsTrigger.id
        updated_trig = {"value": "W1A 1AA"}
        response = self._client.patch("/triggers/%d/" % trig_id,
                                      updated_trig, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete_trigger(self):
        self._asAdmin()
        trig_id = self._joeBloggsTrigger.id
        response = self._client.delete("/triggers/%d/" % trig_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Trigger.objects.filter(id=trig_id).exists(), False)

    def test_user_delete_trigger(self):
        self._asJaneDoe()
        trig_id = self._joeBloggsTrigger.id
        response = self._client.delete("/triggers/%d/" % trig_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_sees_all_triggers(self):
        self._asJaneDoe()
        response = self._client.get('/triggers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        triggers = response.data["results"]
        self.assertEqual(len(triggers), 2)

    def test_user_sees_any_trigger(self):
        self._asJaneDoe()
        trig_id = self._joeBloggsTrigger.id
        response = self._client.get('/triggers/%d/' % trig_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        trig = response.data
        self.assertEqual(trig["id"], self._joeBloggsTrigger.id)
        self.assertEqual(trig["value"], "London")

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

    def test_admin_create_subscription(self):
        self._asAdmin()
        new_sub = {"triggerset_id": self._joeBloggsTriggerSet.id,
                   "user": self._janeDoe.id,
                   "email": True
                   }
        response = self._client.post("/subscriptions/", new_sub, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TriggerSubscription.objects.count(), 4)
        self.assertEqual(TriggerSubscription.objects.filter(user=self._janeDoe).count(), 3)

    def test_user_create_own_subscription(self):
        self._asJaneDoe()
        new_sub = {"triggerset_id": self._joeBloggsTriggerSet.id,
                   "user": self._janeDoe.id,
                   "email": True
                   }
        response = self._client.post("/subscriptions/", new_sub, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TriggerSubscription.objects.count(), 4)
        self.assertEqual(TriggerSubscription.objects.filter(user=self._janeDoe).count(), 3)

    def test_user_create_any_subscription(self):
        self._asJoeBloggs()
        new_sub = {"triggerset_id": self._joeBloggsTriggerSet.id,
                   "user": self._janeDoe.id,
                   "email": True
                   }
        response = self._client.post("/subscriptions/", new_sub, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TriggerSubscription.objects.count(), 3)

    def test_admin_edit_subscription(self):
        self._asAdmin()
        sub_id = self._joeBloggsSubscription.id
        updated_alert = {"email": True}
        response = self._client.patch("/subscriptions/%d/" % sub_id,
                                      updated_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TriggerSubscription.objects.filter(email=True).count(), 1)
        self.assertEqual(TriggerSubscription.objects.get(id=sub_id).email, True)

    def test_user_edit_own_subscription(self):
        self._asJoeBloggs()
        sub_id = self._joeBloggsSubscription.id
        updated_alert = {"email": True}
        response = self._client.patch("/subscriptions/%d/" % sub_id,
                                      updated_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TriggerSubscription.objects.filter(email=True).count(), 1)
        self.assertEqual(TriggerSubscription.objects.get(id=sub_id).email, True)

    def test_user_edit_any_subscription(self):
        self._asJaneDoe()
        sub_id = self._joeBloggsSubscription.id
        updated_alert = {"email": True}
        response = self._client.patch("/subscriptions/%d/" % sub_id,
                                      updated_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_delete_subscription(self):
        self._asAdmin()
        sub_id = self._joeBloggsSubscription.id
        response = self._client.delete("/subscriptions/%d/" % sub_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(TriggerSubscription.objects.filter(id=sub_id).exists(), False)

    def test_user_delete_own_subscription(self):
        self._asJoeBloggs()
        sub_id = self._joeBloggsSubscription.id
        response = self._client.delete("/subscriptions/%d/" % sub_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(TriggerSubscription.objects.filter(id=sub_id).exists(), False)

    def test_user_delete_any_subscription(self):
        self._asJaneDoe()
        sub_id = self._joeBloggsSubscription.id
        response = self._client.delete("/subscriptions/%d/" % sub_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(TriggerSubscription.objects.filter(id=sub_id).exists(), True)

    def test_admin_sees_all_subscriptions(self):
        self._asAdmin()
        response = self._client.get('/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subscriptions = response.data["results"]
        self.assertEqual(len(subscriptions), 3)

    def test_admin_sees_any_subscriptions(self):
        self._asAdmin()
        sub_id = self._joeBloggsSubscription.id
        response = self._client.get('/subscriptions/%d/' % sub_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sub = response.data
        self.assertEqual(sub["id"], self._joeBloggsSubscription.id)
        self.assertEqual(sub["email"], False)

    def test_user_sees_only_own_subscriptions(self):
        self._asJoeBloggs()
        response = self._client.get('/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subscriptions = response.data["results"]
        self.assertEqual(len(subscriptions), 1)
        self.assertEqual(subscriptions[0]["id"], self._joeBloggsSubscription.id)

    def test_user_sees_own_subscription(self):
        self._asJoeBloggs()
        sub_id = self._joeBloggsSubscription.id
        response = self._client.get('/subscriptions/%d/' % sub_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sub = response.data
        self.assertEqual(sub["id"], self._joeBloggsSubscription.id)
        self.assertEqual(sub["email"], False)

    def test_user_sees_any_subscription(self):
        self._asJaneDoe()
        sub_id = self._joeBloggsSubscription.id
        response = self._client.get('/subscriptions/%d/' % sub_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_email_template(self):
        fired = datetime.datetime.now()
        text = self._joeBloggsTriggerSet._complete_email_template(self._joeBloggsAddress, fired)
        self.assertEqual(text, "%s: %s instance %s triggered on %s." % (
            repr(self._joeBloggsTriggerSet.name),
            repr(self._joeBloggsTriggerSet.model),
            repr(self._joeBloggsAddress.id),
            repr(fired.strftime("%Y-%m-%d %H:%M:%S"))
        ))

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
        post_save.connect(receiver=TriggerSet._fire_triggersets, dispatch_uid='Fire Trigger Sets')
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
        post_save.disconnect(receiver=TriggerSet._fire_triggersets,
                             dispatch_uid='Fire Trigger Sets')

    def test_admin_create_alert(self):
        self._asAdmin()
        new_alert = {"user": self._adminUser.id,
                     "status": TriggerAlertStatus.ACTIVE,
                     "last_updated_by": self._adminUser.id
                     }
        response = self._client.post("/alerts/", new_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(TriggerAlertStatus.objects.count(), 0)

    def test_admin_edit_alert(self):
        self._fire_alerts()
        self._asAdmin()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        updated_alert = {"status": TriggerAlertStatus.DISMISSED}
        response = self._client.patch("/alerts/%d/" % joe_alert_id,
                                      updated_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            TriggerAlertStatus.objects.filter(status=TriggerAlertStatus.DISMISSED).count(), 0)

    def test_admin_delete_alert(self):
        self._fire_alerts()
        self._asAdmin()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        response = self._client.delete("/alerts/%d/" % joe_alert_id)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIs(TriggerAlertStatus.objects.filter(id=joe_alert_id).exists(), True)

    def test_admin_sees_all_alerts(self):
        self._fire_alerts()
        self._asAdmin()
        response = self._client.get('/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerts = response.data["results"]
        self.assertEqual(len(alerts), 4)

    def test_admin_sees_any_alert(self):
        self._fire_alerts()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        self._asAdmin()
        response = self._client.get('/alerts/%d/' % joe_alert_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert = response.data
        self.assertEqual(alert["triggeralert"]["instance_id"], self._janeDoeAddress.id)

    def test_user_create_alert(self):
        self._asJaneDoe()
        new_alert = {"user": self._janeDoe.id,
                     "status": TriggerAlertStatus.ACTIVE,
                     "last_updated_by": self._adminUser.id
                     }
        response = self._client.post("/alerts/", new_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(TriggerAlertStatus.objects.count(), 0)

    def test_user_edit_alert(self):
        self._fire_alerts()
        self._asJaneDoe()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        updated_alert = {"status": TriggerAlertStatus.DISMISSED}
        response = self._client.patch("/alerts/%d/" % joe_alert_id,
                                      updated_alert, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            TriggerAlertStatus.objects.filter(status=TriggerAlertStatus.DISMISSED).count(), 0)

    def test_user_delete_alert(self):
        self._fire_alerts()
        self._asJoeBloggs()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        response = self._client.delete("/alerts/%d/" % joe_alert_id)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIs(TriggerAlertStatus.objects.filter(id=joe_alert_id).exists(), True)

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
        self.assertEqual(alert["triggeralert"]["instance_id"], self._janeDoeAddress.id)

    def test_joe_sees_jane_alert(self):
        self._fire_alerts()
        jane_alert_id = self._janeDoeTriggerSet.alerts.all()[0].statuses.all()[0].id
        self._asJoeBloggs()
        response = self._client.get('/alerts/%d/' % jane_alert_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_silence_any_alert(self):
        self._fire_alerts()
        self._asAdmin()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        response = self._client.delete("/alerts/%d/silence/" % joe_alert_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TriggerAlertStatus.objects.get(id=joe_alert_id).status,
                         TriggerAlertStatus.SILENCED)

    def test_user_silence_own_alert(self):
        self._fire_alerts()
        self._asJoeBloggs()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        response = self._client.delete("/alerts/%d/silence/" % joe_alert_id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TriggerAlertStatus.objects.get(id=joe_alert_id).status,
                         TriggerAlertStatus.SILENCED)

    def test_user_silence_any_alert(self):
        self._fire_alerts()
        self._asJaneDoe()
        joe_alert_id = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()[0].id
        response = self._client.delete("/alerts/%d/silence/" % joe_alert_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(TriggerAlertStatus.objects.get(id=joe_alert_id).status,
                         TriggerAlertStatus.ACTIVE)

    def test_admin_dismiss_any_alert(self):
        self._fire_alerts()
        self._asAdmin()
        alert_statuses = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()
        joe_alert_status = alert_statuses[0]
        jane_alert_status = alert_statuses[1]
        response = self._client.delete("/alerts/%d/dismiss/" % joe_alert_status.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TriggerAlertStatus.objects.get(id=joe_alert_status.id).status,
                         TriggerAlertStatus.DISMISSED)
        self.assertEqual(TriggerAlertStatus.objects.get(id=jane_alert_status.id).status,
                         TriggerAlertStatus.DISMISSED)

    def test_user_dismiss_own_alert(self):
        self._fire_alerts()
        self._asJoeBloggs()
        alert_statuses = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()
        joe_alert_status = alert_statuses[0]
        jane_alert_status = alert_statuses[1]
        response = self._client.delete("/alerts/%d/dismiss/" % joe_alert_status.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TriggerAlertStatus.objects.get(id=joe_alert_status.id).status,
                         TriggerAlertStatus.DISMISSED)
        self.assertEqual(TriggerAlertStatus.objects.get(id=jane_alert_status.id).status,
                         TriggerAlertStatus.DISMISSED)

    def test_user_dismiss_any_alert(self):
        self._fire_alerts()
        self._asJaneDoe()
        alert_statuses = self._joeBloggsTriggerSet.alerts.all()[0].statuses.all()
        joe_alert_status = alert_statuses[0]
        jane_alert_status = alert_statuses[1]
        response = self._client.delete("/alerts/%d/dismiss/" % joe_alert_status.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(TriggerAlertStatus.objects.get(id=joe_alert_status.id).status,
                         TriggerAlertStatus.ACTIVE)
        self.assertEqual(TriggerAlertStatus.objects.get(id=jane_alert_status.id).status,
                         TriggerAlertStatus.ACTIVE)
