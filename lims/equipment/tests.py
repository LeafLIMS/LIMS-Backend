from .models import Equipment, EquipmentReservation
from lims.inventory.models import Location
from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
import datetime
from django.utils import timezone


class EquipmentTestCase(LoggedInTestCase):
    def setUp(self):
        super(EquipmentTestCase, self).setUp()
        self._location = Location.objects.create(name="Bench", code="B1")
        self._equipmentSequencer = Equipment.objects.create(name="Sequencer",
                                                            location=self._location,
                                                            status="active", can_reserve=True)
        self._equipmentBroken = Equipment.objects.create(name="Duff",
                                                         location=self._location,
                                                         status="broken", can_reserve=False)

    def test_presets(self):
        self.assertIs(Equipment.objects.filter(name="Sequencer").exists(), True)
        equip1 = Equipment.objects.get(name="Sequencer")
        self.assertEqual(equip1.location, self._location)
        self.assertEqual(equip1.status, "active")
        self.assertEqual(equip1.can_reserve, True)
        self.assertIs(Equipment.objects.filter(name="Duff").exists(), True)
        equip1 = Equipment.objects.get(name="Duff")
        self.assertEqual(equip1.location, self._location)
        self.assertEqual(equip1.status, "broken")
        self.assertEqual(equip1.can_reserve, False)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/equipment/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/equipment/%d/' % self._equipmentSequencer.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/equipment/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/equipment/%d/' % self._equipmentSequencer.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/equipment/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        equipment = response.data
        self.assertEqual(len(equipment["results"]), 2)

    def test_user_view_any(self):
        self._asJoeBloggs()
        response = self._client.get('/equipment/%d/' % self._equipmentSequencer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        equip1 = response.data
        self.assertEqual(equip1["name"], "Sequencer")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/equipment/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        equipment = response.data
        self.assertEqual(len(equipment["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/equipment/%d/' % self._equipmentSequencer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        equip1 = response.data
        self.assertEqual(equip1["name"], "Sequencer")

    def test_user_create(self):
        self._asJaneDoe()
        new_equip = {"name": "TestEquip", "location": self._location.id, "status": "idle",
                     "can_reserve": True}
        response = self._client.post("/equipment/", new_equip, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Equipment.objects.filter(name="TestEquip").exists(), False)

    def test_admin_create(self):
        self._asAdmin()
        new_equip = {"name": "TestEquip", "location": self._location.code, "status": "idle",
                     "can_reserve": True}
        response = self._client.post("/equipment/", new_equip, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(Equipment.objects.filter(name="TestEquip").exists(), True)
        equip1 = Equipment.objects.get(name="TestEquip")
        self.assertEqual(equip1.location, self._location)
        self.assertEqual(equip1.status, "idle")
        self.assertEqual(equip1.can_reserve, True)

        # Other user sees the new one too
        self._asJoeBloggs()
        response = self._client.get('/equipment/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        equipment = response.data
        self.assertEqual(len(equipment["results"]), 3)

    def test_user_edit_any(self):
        self._asJaneDoe()
        updated_equip = {"status": "idle"}
        response = self._client.patch("/equipment/%d/" % self._equipmentSequencer.id,
                                      updated_equip, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        group1 = Equipment.objects.get(name="Sequencer")
        self.assertEqual(group1.status, "active")

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_equip = {"status": "idle"}
        response = self._client.patch("/equipment/%d/" % self._equipmentSequencer.id,
                                      updated_equip, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group1 = Equipment.objects.get(name="Sequencer")
        self.assertEqual(group1.status, "idle")

    def test_user_delete_any(self):
        self._asJoeBloggs()
        response = self._client.delete("/equipment/%d/" % self._equipmentSequencer.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Equipment.objects.filter(name="Sequencer").exists(), True)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/equipment/%d/" % self._equipmentSequencer.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Equipment.objects.filter(name="Sequencer").exists(), False)


class EquipmentReservationTestCase(LoggedInTestCase):
    def setUp(self):
        super(EquipmentReservationTestCase, self).setUp()
        self._location = Location.objects.create(name="Bench", code="B1")
        self._equipmentSequencer = Equipment.objects.create(name="Sequencer",
                                                            location=self._location,
                                                            status="active",
                                                            can_reserve=True)
        self._equipmentBroken = Equipment.objects.create(name="Duff",
                                                         location=self._location,
                                                         status="broken", can_reserve=False)
        self._joeReservation = EquipmentReservation.objects.create(
            start=timezone.make_aware(datetime.datetime(2050, 3, 11)),
            end=timezone.make_aware(datetime.datetime(2050, 3, 13)),
            reserved_for="An experiment I'm doing",
            reserved_by=self._joeBloggs,
            equipment_reserved=self._equipmentSequencer,
            is_confirmed=False,
            checked_in=False)
        self._janeReservation = EquipmentReservation.objects.create(
            start=timezone.make_aware(datetime.datetime(2050, 3, 14)),
            end=timezone.make_aware(datetime.datetime(2050, 3, 16)),
            reserved_for="Very important sequencing stuff",
            reserved_by=self._janeDoe,
            equipment_reserved=self._equipmentSequencer,
            is_confirmed=False,
            checked_in=False)

    def test_presets(self):
        self.assertIs(EquipmentReservation.objects.filter(id=self._joeReservation.id).exists(),
                      True)
        res1 = EquipmentReservation.objects.get(id=self._joeReservation.id)
        self.assertEqual(res1.start, timezone.make_aware(datetime.datetime(2050, 3, 11)))
        self.assertEqual(res1.end, timezone.make_aware(datetime.datetime(2050, 3, 13)))
        self.assertEqual(res1.reserved_for, "An experiment I'm doing")
        self.assertEqual(res1.reserved_by, self._joeBloggs)
        self.assertEqual(res1.equipment_reserved, self._equipmentSequencer)
        self.assertEqual(res1.is_confirmed, False)
        self.assertEqual(res1.checked_in, False)
        res1 = EquipmentReservation.objects.get(id=self._janeReservation.id)
        self.assertEqual(res1.start, timezone.make_aware(datetime.datetime(2050, 3, 14)))
        self.assertEqual(res1.end, timezone.make_aware(datetime.datetime(2050, 3, 16)))
        self.assertEqual(res1.reserved_for, "Very important sequencing stuff")
        self.assertEqual(res1.reserved_by, self._janeDoe)
        self.assertEqual(res1.equipment_reserved, self._equipmentSequencer)
        self.assertEqual(res1.is_confirmed, False)
        self.assertEqual(res1.checked_in, False)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/equipmentreservation/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/equipmentreservation/%d/' % self._joeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/equipmentreservation/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/equipmentreservation/%d/' % self._joeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/equipmentreservation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.data
        self.assertEqual(len(res["results"]), 2)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/equipmentreservation/%d/' % self._joeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res1 = response.data
        self.assertEqual(res1["start"], "2050-03-11T00:00:00Z")
        self.assertEqual(res1["end"], "2050-03-13T00:00:00Z")
        self.assertEqual(res1["reserved_for"], "An experiment I'm doing")
        self.assertEqual(res1["reserved_by"], self._joeBloggs.username)
        self.assertEqual(res1["equipment_reserved"], self._equipmentSequencer.name)
        self.assertEqual(res1["is_confirmed"], False)
        self.assertEqual(res1["checked_in"], False)

    def test_user_view_any(self):
        self._asJoeBloggs()
        response = self._client.get('/equipmentreservation/%d/' % self._janeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res1 = response.data
        self.assertEqual(res1["start"], "2050-03-14T00:00:00Z")
        self.assertEqual(res1["end"], "2050-03-16T00:00:00Z")
        self.assertEqual(res1["reserved_for"], "Very important sequencing stuff")
        self.assertEqual(res1["reserved_by"], self._janeDoe.username)
        self.assertEqual(res1["equipment_reserved"], self._equipmentSequencer.name)
        self.assertEqual(res1["is_confirmed"], False)
        self.assertEqual(res1["checked_in"], False)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/equipmentreservation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.data
        self.assertEqual(len(res["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/equipmentreservation/%d/' % self._janeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res1 = response.data
        self.assertEqual(res1["start"], "2050-03-14T00:00:00Z")
        self.assertEqual(res1["end"], "2050-03-16T00:00:00Z")
        self.assertEqual(res1["reserved_for"], "Very important sequencing stuff")
        self.assertEqual(res1["reserved_by"], self._janeDoe.username)
        self.assertEqual(res1["equipment_reserved"], self._equipmentSequencer.name)
        self.assertEqual(res1["is_confirmed"], False)
        self.assertEqual(res1["checked_in"], False)

    def test_user_create_own(self):
        self._asJoeBloggs()
        new_res = {"start": timezone.make_aware(datetime.datetime(2050, 6, 14)),
                   "end": timezone.make_aware(datetime.datetime(2050, 6, 16)),
                   "reserved_for": "Something or other I might want to do",
                   "reserved_by": self._joeBloggs.username,
                   "equipment_reserved": self._equipmentSequencer.name,
                   "is_confirmed": False,
                   "checked_in": False}
        response = self._client.post("/equipmentreservation/", new_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Something or other I might want to do").exists(), True)
        res1 = EquipmentReservation.objects.get(
            reserved_for="Something or other I might want to do")
        self.assertEqual(res1.start, timezone.make_aware(datetime.datetime(2050, 6, 14)))
        self.assertEqual(res1.end, timezone.make_aware(datetime.datetime(2050, 6, 16)))
        self.assertEqual(res1.reserved_by, self._joeBloggs)
        self.assertEqual(res1.equipment_reserved, self._equipmentSequencer)
        self.assertEqual(res1.is_confirmed, False)
        self.assertEqual(res1.checked_in, False)
        # New one shows up in list of all reservations
        response = self._client.get('/equipmentreservation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.data
        self.assertEqual(len(res["results"]), 3)

    def test_user_create_other(self):
        self._asJoeBloggs()
        new_res = {"start": timezone.make_aware(datetime.datetime(2050, 6, 14)),
                   "end": timezone.make_aware(datetime.datetime(2050, 6, 16)),
                   "reserved_for": "Something or other I might want to do",
                   "reserved_by": self._janeDoe.username,
                   "equipment_reserved": self._equipmentSequencer.name,
                   "is_confirmed": False,
                   "checked_in": False}
        response = self._client.post("/equipmentreservation/", new_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Something or other I might want to do").exists(), False)

    def test_admin_create(self):
        self._asAdmin()
        new_res = {"start": timezone.make_aware(datetime.datetime(2050, 6, 14)),
                   "end": timezone.make_aware(datetime.datetime(2050, 6, 16)),
                   "reserved_for": "Something or other I might want to do",
                   "reserved_by": self._joeBloggs.username,
                   "equipment_reserved": self._equipmentSequencer.name,
                   "is_confirmed": False,
                   "checked_in": False}
        response = self._client.post("/equipmentreservation/", new_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Something or other I might want to do").exists(), True)
        res1 = EquipmentReservation.objects.get(
            reserved_for="Something or other I might want to do")
        self.assertEqual(res1.start, timezone.make_aware(datetime.datetime(2050, 6, 14)))
        self.assertEqual(res1.end, timezone.make_aware(datetime.datetime(2050, 6, 16)))
        self.assertEqual(res1.reserved_by, self._joeBloggs)
        self.assertEqual(res1.equipment_reserved, self._equipmentSequencer)
        self.assertEqual(res1.is_confirmed, False)
        self.assertEqual(res1.checked_in, False)
        # New one shows up in list of all reservations, even for other users
        self._asJoeBloggs()
        response = self._client.get('/equipmentreservation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.data
        self.assertEqual(len(res["results"]), 3)

    def test_user_edit_own(self):
        self._asJoeBloggs()
        updated_res = {"reserved_for": "You want more detail so here it is"}
        response = self._client.patch("/equipmentreservation/%d/" % self._joeReservation.id,
                                      updated_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._joeReservation.reserved_for, "You want more detail so here it is")

    def test_user_edit_any(self):
        self._asJaneDoe()
        updated_res = {"reserved_for": "You want more detail so here it is"}
        response = self._client.patch("/equipmentreservation/%d/" % self._janeReservation.id,
                                      updated_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self._joeReservation.reserved_for, "Very important sequencing stuff")

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_res = {"reserved_for": "You want more detail so here it is"}
        response = self._client.patch("/equipmentreservation/%d/" % self._joeReservation.id,
                                      updated_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._joeReservation.reserved_for, "You want more detail so here it is")

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/equipmentreservation/%d/" % self._janeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Very important sequencing stuff").exists(), False)

    def test_user_delete_any(self):
        self._asJoeBloggs()
        response = self._client.delete("/equipmentreservation/%d/" % self._janeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Very important sequencing stuff").exists(), True)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/equipmentreservation/%d/" % self._janeReservation.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Very important sequencing stuff").exists(), False)

    def test_staff_create_autoconfirm(self):
        self._asStaff()
        new_res = {"start": timezone.make_aware(datetime.datetime(2050, 6, 14)),
                   "end": timezone.make_aware(datetime.datetime(2050, 6, 16)),
                   "reserved_for": "Something or other I might want to do",
                   "reserved_by": self._staffUser.username,
                   "equipment_reserved": self._equipmentSequencer.name,
                   "is_confirmed": False,
                   "checked_in": False}
        response = self._client.post("/equipmentreservation/", new_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Something or other I might want to do").exists(), True)
        res1 = EquipmentReservation.objects.get(
            reserved_for="Something or other I might want to do")
        self.assertEqual(res1.is_confirmed, True)
        self.assertEqual(res1.confirmed_by, self._staffUser)

    def test_start_after_end(self):
        self._asJoeBloggs()
        new_res = {"start": timezone.make_aware(datetime.datetime(2050, 9, 12)),
                   "end": timezone.make_aware(datetime.datetime(2050, 6, 15)),
                   "reserved_for": "Something or other I might want to do",
                   "reserved_by": self._joeBloggs.username,
                   "equipment_reserved": self._equipmentSequencer.name,
                   "is_confirmed": False,
                   "checked_in": False}
        response = self._client.post("/equipmentreservation/", new_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Something or other I might want to do").exists(), False)

    def test_overlapping_reservation_date_and_equipment(self):
        self._asJoeBloggs()
        new_res = {"start": timezone.make_aware(datetime.datetime(2050, 3, 12)),
                   "end": timezone.make_aware(datetime.datetime(2050, 3, 15)),
                   "reserved_for": "Something or other I might want to do",
                   "reserved_by": self._joeBloggs.username,
                   "equipment_reserved": self._equipmentSequencer.name,
                   "is_confirmed": False,
                   "checked_in": False}
        response = self._client.post("/equipmentreservation/", new_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIs(EquipmentReservation.objects.filter(
            reserved_for="Something or other I might want to do").exists(), False)

    def test_overlapping_reservation_date_not_equipment(self):
        self._asJoeBloggs()
        new_res = {"start": timezone.make_aware(datetime.datetime(2050, 3, 12)),
                   "end": timezone.make_aware(datetime.datetime(2050, 3, 15)),
                   "reserved_for": "Something or other I might want to do",
                   "reserved_by": self._joeBloggs.username,
                   "equipment_reserved": self._equipmentBroken.name,
                   "is_confirmed": False,
                   "checked_in": False}
        response = self._client.post("/equipmentreservation/", new_res, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
