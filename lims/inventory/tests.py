from lims.shared.loggedintestcase import LoggedInTestCase
from lims.filetemplate.models import FileTemplate, FileTemplateField
from rest_framework import status
from .models import Location, ItemType, AmountMeasure, Set, Item, Tag
from django.contrib.auth.models import Permission, Group
from .views import ViewPermissionsMixin
import os


class LocationTestCase(LoggedInTestCase):
    def setUp(self):
        super(LocationTestCase, self).setUp()

        self._top = Location.objects.create(name="Top", code="T", parent=None)
        self._middle = Location.objects.create(name="Middle", code="M", parent=self._top)
        self._top.children.add(self._middle)
        self._bottom = Location.objects.create(name="Bottom", code="B", parent=self._middle)
        self._middle.children.add(self._bottom)

    def test_presets(self):
        t = Location.objects.get(name="Top")
        self.assertEqual(t.code, "T")
        self.assertIsNone(t.parent)
        self.assertIs(t.has_children(), True)
        self.assertEqual(t.children.count(), 1)
        self.assertEqual(t.children.all()[0], self._middle)
        m = Location.objects.get(name="Middle")
        self.assertEqual(m.code, "M")
        self.assertEqual(m.parent, self._top)
        self.assertIs(m.has_children(), True)
        self.assertEqual(m.children.count(), 1)
        self.assertEqual(m.children.all()[0], self._bottom)
        b = Location.objects.get(name="Bottom")
        self.assertEqual(b.code, "B")
        self.assertEqual(b.parent, self._middle)
        self.assertIs(b.has_children(), False)
        self.assertEqual(b.children.count(), 0)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/locations/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/locations/%d/' % self._top.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/locations/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/locations/%d/' % self._top.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        locations = response.data
        self.assertEqual(len(locations["results"]), 4)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        locations = response.data
        self.assertEqual(len(locations["results"]), 4)

    def test_user_view(self):
        self._asJaneDoe()
        response = self._client.get('/locations/%d/' % self._middle.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        loc = response.data
        self.assertEqual(loc["name"], "Middle")
        self.assertEqual(loc["code"], "M")
        self.assertEqual(loc["has_children"], True)
        self.assertEqual(loc["parent"], self._top.code)

    def test_admin_view(self):
        self._asAdmin()
        response = self._client.get('/locations/%d/' % self._middle.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        loc = response.data
        self.assertEqual(loc["name"], "Middle")
        self.assertEqual(loc["code"], "M")
        self.assertEqual(loc["has_children"], True)
        self.assertEqual(loc["parent"], self._top.code)

    def test_user_create(self):
        self._asJaneDoe()
        new_location = {"name": "Test", "code": "X", "parent": self._top.code}
        response = self._client.post("/locations/", new_location, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # The DB should still only have 3 locations
        self.assertEqual(Location.objects.count(), 4)

    def test_admin_create(self):
        self._asAdmin()
        new_location = {"name": "Test", "code": "X", "parent": self._top.code}
        response = self._client.post("/locations/", new_location, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Location.objects.count(), 5)
        self.assertIs(Location.objects.filter(name="Test").exists(), True)
        loc = Location.objects.get(name="Test")
        self.assertEqual(loc.code, "X")
        self.assertEqual(loc.parent, self._top)

    def test_user_edit(self):
        self._asJoeBloggs()
        updated_location = {"code": "Y"}
        response = self._client.patch("/locations/%d/" % self._top.id,
                                      updated_location, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Location.objects.filter(code="T").exists(), True)
        self.assertIs(Location.objects.filter(code="Y").exists(), False)

    def test_admin_edit(self):
        self._asAdmin()
        updated_location = {"code": "Y"}
        response = self._client.patch("/locations/%d/" % self._top.id,
                                      updated_location, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(Location.objects.filter(code="T").exists(), False)
        self.assertIs(Location.objects.filter(code="Y").exists(), True)
        t = Location.objects.get(name="Top")
        self.assertEqual(t.code, "Y")

    def test_user_delete(self):
        self._asJoeBloggs()
        response = self._client.delete("/locations/%d/" % self._bottom.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Location.objects.filter(name="Bottom").exists(), True)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete("/locations/%d/" % self._bottom.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Location.objects.filter(name="Bottom").exists(), False)
        m = Location.objects.get(name="Middle")
        self.assertIs(m.has_children(), False)
        self.assertEqual(m.children.count(), 0)

    def test_location_display_name(self):
        self.assertEqual(self._top.display_name(), '%s' % self._top.name)
        self.assertEqual(self._middle.display_name(), '-- %s' % self._middle.name)
        self.assertEqual(self._bottom.display_name(), '---- %s' % self._bottom.name)

    def test_location_str(self):
        self.assertEqual(self._top.__str__(), '%s' % self._top.name)
        self.assertEqual(self._middle.__str__(), '%s (%s)' % (self._middle.name, self._top.name))
        self.assertEqual(self._bottom.__str__(), '%s (%s)' % (self._bottom.name, self._middle.name))


class ItemTypeTestCase(LoggedInTestCase):
    def setUp(self):
        super(ItemTypeTestCase, self).setUp()

        self._top = ItemType.objects.create(name="Top", parent=None)
        self._middle = ItemType.objects.create(name="Middle", parent=self._top)
        self._top.children.add(self._middle)
        self._bottom = ItemType.objects.create(name="Bottom", parent=self._middle)
        self._middle.children.add(self._bottom)

    def test_presets(self):
        t = ItemType.objects.get(name="Top")
        self.assertIsNone(t.parent)
        self.assertIs(t.has_children(), True)
        self.assertEqual(t.children.count(), 1)
        self.assertEqual(t.children.all()[0], self._middle)
        m = ItemType.objects.get(name="Middle")
        self.assertEqual(m.parent, self._top)
        self.assertIs(m.has_children(), True)
        self.assertEqual(m.children.count(), 1)
        self.assertEqual(m.children.all()[0], self._bottom)
        b = ItemType.objects.get(name="Bottom")
        self.assertEqual(b.parent, self._middle)
        self.assertIs(b.has_children(), False)
        self.assertEqual(b.children.count(), 0)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/itemtypes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/itemtypes/%d/' % self._top.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/itemtypes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/itemtypes/%d/' % self._top.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/itemtypes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        itemtypes = response.data
        self.assertEqual(len(itemtypes["results"]), 4)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/itemtypes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        itemtypes = response.data
        self.assertEqual(len(itemtypes["results"]), 4)

    def test_user_view(self):
        self._asJaneDoe()
        response = self._client.get('/itemtypes/%d/' % self._middle.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        it = response.data
        self.assertEqual(it["name"], "Middle")
        self.assertEqual(it["has_children"], True)
        self.assertEqual(it["parent"], self._top.name)

    def test_admin_view(self):
        self._asAdmin()
        response = self._client.get('/itemtypes/%d/' % self._middle.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        it = response.data
        self.assertEqual(it["name"], "Middle")
        self.assertEqual(it["has_children"], True)
        self.assertEqual(it["parent"], self._top.name)

    def test_user_create(self):
        self._asJaneDoe()
        new_it = {"name": "Test", "parent": self._top.name}
        response = self._client.post("/itemtypes/", new_it, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # The DB should still only have 4 itemtypes
        self.assertEqual(ItemType.objects.count(), 4)

    def test_admin_create(self):
        self._asAdmin()
        new_it = {"name": "Test", "parent": self._top.name}
        response = self._client.post("/itemtypes/", new_it, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ItemType.objects.count(), 5)
        self.assertIs(ItemType.objects.filter(name="Test").exists(), True)
        it = ItemType.objects.get(name="Test")
        self.assertEqual(it.parent, self._top)

    def test_user_edit(self):
        self._asJoeBloggs()
        updated_it = {"parent": None}
        response = self._client.patch("/itemtypes/%d/" % self._bottom.id,
                                      updated_it, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(ItemType.objects.filter(parent=None).count(), 2)

    def test_admin_edit(self):
        self._asAdmin()
        updated_it = {"parent": None}
        response = self._client.patch("/itemtypes/%d/" % self._bottom.id,
                                      updated_it, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(ItemType.objects.filter(parent=None).count(), 3)
        b = ItemType.objects.get(name="Bottom")
        self.assertIsNone(b.parent)
        m = ItemType.objects.get(name="Middle")
        self.assertEqual(m.children.count(), 0)
        self.assertIs(m.has_children(), False)

    def test_user_delete(self):
        self._asJoeBloggs()
        response = self._client.delete("/itemtypes/%d/" % self._bottom.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(ItemType.objects.filter(name="Bottom").exists(), True)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete("/itemtypes/%d/" % self._bottom.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(ItemType.objects.filter(name="Bottom").exists(), False)
        m = ItemType.objects.get(name="Middle")
        self.assertIs(m.has_children(), False)
        self.assertEqual(m.children.count(), 0)

    def test_itemtype_display_name(self):
        self.assertEqual(self._top.display_name(), '%s' % self._top.name)
        self.assertEqual(self._middle.display_name(), '-- %s' % self._middle.name)
        self.assertEqual(self._bottom.display_name(), '---- %s' % self._bottom.name)

    def test_itemtype_root(self):
        self.assertEqual(self._top.root(), self._top.name)
        self.assertEqual(self._middle.root(), self._top.name)
        self.assertEqual(self._bottom.root(), self._top.name)
        self._middle.children.remove(self._bottom)
        self._bottom.parent = None
        self.assertEqual(self._bottom.root(), self._bottom.name)


class AmountMeasureTestCase(LoggedInTestCase):
    def setUp(self):
        super(AmountMeasureTestCase, self).setUp()

        self._millilitre, c = AmountMeasure.objects.get_or_create(name="Millilitres", symbol="ml")
        self._gram, c = AmountMeasure.objects.get_or_create(name="Gram", symbol="g")

    def test_presets(self):
        ml = AmountMeasure.objects.get(name="Millilitres")
        self.assertEqual(ml.symbol, "ml")
        g = AmountMeasure.objects.get(name="Gram")
        self.assertEqual(g.symbol, "g")

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/measures/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/measures/%d/' % self._millilitre.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/measures/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/measures/%d/' % self._millilitre.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        self._asJoeBloggs()
        response = self._client.get('/measures/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        measures = response.data
        self.assertEqual(len(measures["results"]), 15)

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/measures/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        measures = response.data
        self.assertEqual(len(measures["results"]), 15)

    def test_user_view(self):
        self._asJaneDoe()
        response = self._client.get('/measures/%d/' % self._millilitre.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ml = response.data
        self.assertEqual(ml["name"], "Millilitres")
        self.assertEqual(ml["symbol"], "ml")

    def test_admin_view(self):
        self._asAdmin()
        response = self._client.get('/measures/%d/' % self._millilitre.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ml = response.data
        self.assertEqual(ml["name"], "Millilitres")
        self.assertEqual(ml["symbol"], "ml")

    def test_user_create(self):
        self._asJaneDoe()
        new_amt = {"name": "Blob", "symbol": "b"}
        response = self._client.post("/measures/", new_amt, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # The DB should still only have 2 measures
        self.assertEqual(AmountMeasure.objects.count(), 26)

    def test_admin_create(self):
        self._asAdmin()
        new_amt = {"name": "Blob", "symbol": "b"}
        response = self._client.post("/measures/", new_amt, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AmountMeasure.objects.count(), 27)
        self.assertIs(AmountMeasure.objects.filter(name="Blob").exists(), True)
        b = AmountMeasure.objects.get(name="Blob")
        self.assertEqual(b.symbol, "b")

    def test_user_edit(self):
        self._asJoeBloggs()
        updated_amt = {"symbol": "x"}
        response = self._client.patch("/measures/%d/" % self._millilitre.id,
                                      updated_amt, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(AmountMeasure.objects.filter(symbol="x").count(), 0)
        self.assertIs(AmountMeasure.objects.filter(symbol="ml").count(), 1)

    def test_admin_edit(self):
        self._asAdmin()
        updated_amt = {"symbol": "x"}
        response = self._client.patch("/measures/%d/" % self._millilitre.id,
                                      updated_amt, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(AmountMeasure.objects.filter(symbol="x").count(), 1)
        self.assertIs(AmountMeasure.objects.filter(symbol="ml").count(), 0)

    def test_user_delete(self):
        self._asJoeBloggs()
        response = self._client.delete("/measures/%d/" % self._gram.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(AmountMeasure.objects.filter(name="Gram").exists(), True)

    def test_admin_delete(self):
        self._asAdmin()
        response = self._client.delete("/measures/%d/" % self._gram.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(AmountMeasure.objects.filter(name="Gram").exists(), False)

    def test_amountmeasure_str(self):
        self.assertEqual(self._millilitre.__str__(), "Millilitres (ml)")


class SetTestCase(LoggedInTestCase):
    def setUp(self):
        super(SetTestCase, self).setUp()

        self._set1 = Set.objects.create(name="Set1", is_public=True, is_partset=True)
        self._set2 = Set.objects.create(name="Set2", is_public=True, is_partset=True)

        self._measure = AmountMeasure.objects.create(name="Blob", symbol="b")
        self._location = Location.objects.create(name="On top of the cupboard", code="L1")

        self._itemtype1 = ItemType.objects.create(name="Type1", parent=None)
        self._itemtype2 = ItemType.objects.create(name="Type2", parent=self._itemtype1)
        self._itemtype3 = ItemType.objects.create(name="Type3", parent=self._itemtype2)

        self._item1 = Item.objects.create(name="Item1",
                                          identifier="I1",
                                          description="Complicated",
                                          item_type=self._itemtype1,
                                          in_inventory=True,
                                          amount_available=5,
                                          amount_measure=self._measure,
                                          location=self._location,
                                          added_by=self._joeBloggs)
        self._item2 = Item.objects.create(name="Item2",
                                          identifier="I2",
                                          description="Even more complicated",
                                          item_type=self._itemtype2,
                                          in_inventory=True,
                                          amount_available=3,
                                          amount_measure=self._measure,
                                          location=self._location,
                                          added_by=self._joeBloggs)
        self._item3 = Item.objects.create(name="Item3",
                                          identifier="I3",
                                          description="Less complicated",
                                          item_type=self._itemtype3,
                                          in_inventory=True,
                                          amount_available=2,
                                          amount_measure=self._measure,
                                          location=self._location,
                                          added_by=self._janeDoe)
        self._item4 = Item.objects.create(name="Item4",
                                          identifier="I4",
                                          description="Not complicated",
                                          item_type=self._itemtype3,
                                          in_inventory=True,
                                          amount_available=2,
                                          amount_measure=self._measure,
                                          location=self._location,
                                          added_by=self._janeDoe)

        # Joe's set = 1+2
        self._set1.items.add(self._item1)
        self._set1.items.add(self._item2)

        # Jane's set = 1+3+4
        self._set2.items.add(self._item1)
        self._set2.items.add(self._item3)
        self._set2.items.add(self._item4)

        # We have to simulate giving Joe and Jane's groups access to these sets. Joe can see and
        # edit only set 1.
        # Jane can see and edit set 2, and see set 1 but not edit it.
        ViewPermissionsMixin().assign_permissions(instance=self._set1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._set2,
                                                  permissions={"jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._item1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._item2,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._item3,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._item4,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "rw"})

        # We also have to give Joe and Jane permission to view, change and delete sets in
        # general.
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="add_set"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="view_set"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="change_set"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="delete_set"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="add_set"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_set"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="change_set"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="delete_set"))

    def test_presets(self):
        self.assertIs(Set.objects.filter(name="Set1").exists(), True)
        s = Set.objects.get(name="Set1")
        self.assertIs(s.is_public, True)
        self.assertIs(s.is_partset, True)
        self.assertEqual(s.items.count(), 2)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item2]))
        self.assertIs(Set.objects.filter(name="Set2").exists(), True)
        s = Set.objects.get(name="Set2")
        self.assertIs(s.is_public, True)
        self.assertIs(s.is_partset, True)
        self.assertEqual(s.items.count(), 3)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item3, self._item4]))

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/inventorysets/%d/' % self._set1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/inventorysets/%d/' % self._set1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see projects in his own group
        self._asJoeBloggs()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sets = response.data
        self.assertEqual(len(sets["results"]), 1)
        s = sets["results"][0]
        self.assertEqual(s["name"], "Set1")

    def test_user_list_group(self):
        # Jane can see both because her group has read permission to Joe's project
        self._asJaneDoe()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sets = response.data
        self.assertEqual(len(sets["results"]), 2)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/inventorysets/%d/' % self._set1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = response.data
        self.assertEqual(s["name"], "Set1")

    def test_user_view_other(self):
        # Jane's project is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/inventorysets/%d/' % self._set2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's project
        self._asJaneDoe()
        response = self._client.get('/inventorysets/%d/' % self._set1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = response.data
        self.assertEqual(s["name"], "Set1")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sets = response.data
        self.assertEqual(len(sets["results"]), 2)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/inventorysets/%d/' % self._set2.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = response.data
        self.assertEqual(s["name"], "Set2")

    def test_user_create_own(self):
        self._asJaneDoe()
        new_set = {"name": "Set3",
                   "is_public": True,
                   "is_partset": False,
                   "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/inventorysets/", new_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Set.objects.count(), 3)
        self.assertIs(Set.objects.filter(name="Set3").exists(), True)
        s = Set.objects.get(name="Set3")
        self.assertIs(s.is_public, True)
        self.assertIs(s.is_partset, False)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sets = response.data
        self.assertEqual(len(sets["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sets = response.data
        self.assertEqual(len(sets["results"]), 3)

    def test_admin_create_any(self):
        # Admin should be able to create a set
        self._asAdmin()
        new_set = {"name": "Set3",
                   "is_public": True,
                   "is_partset": False,
                   "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/inventorysets/", new_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Set.objects.count(), 3)
        self.assertIs(Set.objects.filter(name="Set3").exists(), True)
        s = Set.objects.get(name="Set3")
        self.assertIs(s.is_public, True)
        self.assertIs(s.is_partset, False)

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sets = response.data
        self.assertEqual(len(sets["results"]), 1)
        self._asJaneDoe()
        response = self._client.get('/inventorysets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sets = response.data
        self.assertEqual(len(sets["results"]), 3)

    def test_user_edit_own(self):
        self._asJoeBloggs()
        updated_set = {"is_partset": False}
        response = self._client.patch("/inventorysets/%d/" % self._set1.id,
                                      updated_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertIs(s.is_partset, False)

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's project
        self._asJoeBloggs()
        updated_set = {"is_partset": False}
        response = self._client.patch("/inventorysets/%d/" % self._set2.id,
                                      updated_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        s = Set.objects.get(name="Set2")
        self.assertIs(s.is_partset, True)

    def test_user_edit_other_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        updated_set = {"is_partset": False}
        response = self._client.patch("/inventorysets/%d/" % self._set1.id,
                                      updated_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        s = Set.objects.get(name="Set1")
        self.assertIs(s.is_partset, True)

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's set first so she can edit it
        ViewPermissionsMixin().assign_permissions(instance=self._set1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        updated_set = {"is_partset": False}
        response = self._client.patch("/inventorysets/%d/" % self._set1.id,
                                      updated_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertIs(s.is_partset, False)

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_set = {"is_partset": False}
        response = self._client.patch("/inventorysets/%d/" % self._set1.id,
                                      updated_set, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertIs(s.is_partset, False)

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/inventorysets/%d/" % self._set2.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Set.objects.filter(name="Set2").exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/inventorysets/%d/" % self._set2.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Set.objects.filter(name="Set2").exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/inventorysets/%d/" % self._set1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Set.objects.filter(name="Set1").exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._set1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/inventorysets/%d/" % self._set1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Set.objects.filter(name="Set1").exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/inventorysets/%d/" % self._set1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Set.objects.filter(name="Set1").exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own sets
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch(
            "/inventorysets/%d/set_permissions/" % self._set1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        permissions = {"jane_group": "r"}
        response = self._client.patch(
            "/inventorysets/%d/set_permissions/" % self._set2.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        s = Set.objects.get(name="Set2")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch(
            "/inventorysets/%d/set_permissions/" % self._set1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._set1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/inventorysets/%d/set_permissions/" % self._set1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_admin_set_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/inventorysets/%d/set_permissions/" % self._set1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_set_permissions_invalid_group(self):
        # An invalid group should throw a 400 data error
        self._asAdmin()
        permissions = {"jim_group": "r"}
        response = self._client.patch(
            "/inventorysets/%d/set_permissions/" % self._set1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch(
            "/inventorysets/%d/set_permissions/" % self._set1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the permission wasn't changed accidentally in the process
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/inventorysets/%d/remove_permissions/?groups=joe_group" % self._set1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        response = self._client.delete(
            "/inventorysets/%d/remove_permissions/?groups=jane_group" % self._set2.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        s = Set.objects.get(name="Set2")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        response = self._client.delete(
            "/inventorysets/%d/remove_permissions/?groups=joe_group" % self._set1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._set1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/inventorysets/%d/remove_permissions/?groups=joe_group" % self._set1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/inventorysets/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._set1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = Set.objects.get(name="Set1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="jane_group")), None)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=s,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_remove_permissions_invalid_group(self):
        # An invalid group name should fail quietly - we don't care if permissions can't be
        # removed as the end result is the same, i.e. that group can't access anything
        self._asAdmin()
        response = self._client.delete(
            "/inventorysets/%d/remove_permissions/?groups=jim_group" %
            self._set1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_user_add_item_own(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/inventorysets/%d/add/?id=%s" % (self._set1.id, self._item3.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 3)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item2, self._item3]))

    def test_user_add_item_nonread(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/inventorysets/%d/add/?id=%s" % (self._set2.id, self._item2.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        s = Set.objects.get(name="Set2")
        self.assertEqual(s.items.count(), 3)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item3, self._item4]))

    def test_user_add_item_readonly(self):
        self._asJaneDoe()
        response = self._client.post(
            "/inventorysets/%d/add/?id=%s" % (self._set1.id, self._item3.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 2)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item2]))

    def test_user_add_item_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._set1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.post(
            "/inventorysets/%d/add/?id=%s" % (self._set1.id, self._item3.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 3)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item2, self._item3]))

    def test_admin_add_item_any(self):
        self._asAdmin()
        response = self._client.post(
            "/inventorysets/%d/add/?id=%s" % (self._set1.id, self._item3.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 3)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item2, self._item3]))

    def test_add_item_invalid_id(self):
        self._asJoeBloggs()
        response = self._client.post("/inventorysets/%d/add/?id=%s" % (self._set1.id, 99999),
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 2)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item2]))

    def test_add_item_missing_id(self):
        self._asJoeBloggs()
        response = self._client.post("/inventorysets/%d/add/" % self._set1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_remove_item_own(self):
        self._asJoeBloggs()
        response = self._client.delete(
            "/inventorysets/%d/remove/?id=%s" % (self._set1.id, self._item1.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 1)
        self.assertEqual(set(s.items.all()), set([self._item2]))

    def test_user_remove_item_nonread(self):
        self._asJoeBloggs()
        response = self._client.delete(
            "/inventorysets/%d/remove/?id=%s" % (self._set2.id, self._item1.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        s = Set.objects.get(name="Set2")
        self.assertEqual(s.items.count(), 3)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item3, self._item4]))

    def test_user_remove_item_readonly(self):
        self._asJaneDoe()
        response = self._client.delete(
            "/inventorysets/%d/remove/?id=%s" % (self._set1.id, self._item1.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 2)
        self.assertEqual(set(s.items.all()), set([self._item1, self._item2]))

    def test_user_remove_item_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._set1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/inventorysets/%d/remove/?id=%s" % (self._set1.id, self._item1.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 1)
        self.assertEqual(set(s.items.all()), set([self._item2]))

    def test_admin_remove_item_any(self):
        self._asAdmin()
        response = self._client.delete(
            "/inventorysets/%d/remove/?id=%s" % (self._set1.id, self._item2.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        s = Set.objects.get(name="Set1")
        self.assertEqual(s.items.count(), 1)
        self.assertEqual(set(s.items.all()), set([self._item1]))

    def test_remove_item_invalid_id(self):
        self._asJoeBloggs()
        response = self._client.delete("/inventorysets/%d/remove/?id=%s" % (self._set1.id, 99999),
                                       format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_item_missing_id(self):
        self._asJoeBloggs()
        response = self._client.delete("/inventorysets/%d/remove/" % self._set1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_item_id_not_in_set(self):
        self._asJoeBloggs()
        response = self._client.delete(
            "/inventorysets/%d/remove/?id=%s" % (self._set1.id, self._item3.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_number_of_items(self):
        self.assertEqual(self._set1.number_of_items(), 2)
        self.assertEqual(self._set2.number_of_items(), 3)

    def test_user_listitems_own(self):
        self._asJoeBloggs()
        response = self._client.get("/inventorysets/%d/items/" % self._set1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items), 2)
        self.assertEqual(set([items[0]["name"], items[1]["name"]]), set(["Item1", "Item2"]))

    def test_user_listitems_nonread(self):
        self._asJoeBloggs()
        response = self._client.get("/inventorysets/%d/items/" % self._set2.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_listitems_read(self):
        self._asJaneDoe()
        response = self._client.get("/inventorysets/%d/items/" % self._set1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items), 2)
        self.assertEqual(set([items[0]["name"], items[1]["name"]]), set(["Item1", "Item2"]))

    def test_admin_listitems_any(self):
        self._asAdmin()
        response = self._client.get("/inventorysets/%d/items/" % self._set1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items), 2)
        self.assertEqual(set([items[0]["name"], items[1]["name"]]), set(["Item1", "Item2"]))

    def test_listitems_limit_to(self):
        self._asJaneDoe()
        limit = {"limit_to": self._itemtype3.name}
        response = self._client.get("/inventorysets/%d/items/" % self._set2.id, limit,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items), 2)
        self.assertEqual(set([items[0]["name"], items[1]["name"]]), set(["Item3", "Item4"]))
        limit = {"limit_to": self._itemtype1.name}
        response = self._client.get("/inventorysets/%d/items/" % self._set2.id, limit,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items), 1)
        self.assertEqual(set([items[0]["name"]]), set(["Item1"]))


class ItemTestCase(LoggedInTestCase):
    def setUp(self):
        super(ItemTestCase, self).setUp()

        self._measure, c = AmountMeasure.objects.get_or_create(name="Litres", symbol="l")
        self._measure2, c = AmountMeasure.objects.get_or_create(name="Millilitres", symbol="ml")
        self._measure3 = AmountMeasure.objects.create(name="Nanograms/microlitre", symbol="ng/ul")
        self._location = Location.objects.create(name="On top of the cupboard", code="L1")
        self._location2 = Location.objects.create(name="On a shelf", code="L2",
                                                  parent=self._location)

        self._itemtype1 = ItemType.objects.create(name="Type1", parent=None)
        self._itemtype2 = ItemType.objects.create(name="Type2", parent=self._itemtype1)
        self._itemtype3 = ItemType.objects.create(name="Type3", parent=self._itemtype2)

        self._item1 = Item.objects.create(name="Item1",
                                          identifier="I1",
                                          description="Complicated",
                                          item_type=self._itemtype1,
                                          amount_available=5,
                                          amount_measure=self._measure,
                                          location=self._location2,
                                          added_by=self._joeBloggs)
        self._item1.tags.add(Tag.objects.create(name="hello"))
        self._item1.tags.add(Tag.objects.create(name="world"))
        self._item2 = Item.objects.create(name="Item2",
                                          identifier="I2",
                                          description="Even more complicated",
                                          item_type=self._itemtype2,
                                          amount_available=3,
                                          amount_measure=self._measure,
                                          concentration=0.5,
                                          concentration_measure=self._measure3,
                                          location=self._location,
                                          added_by=self._joeBloggs)
        self._item3 = Item.objects.create(name="Item3",
                                          identifier="I3",
                                          description="Less complicated",
                                          item_type=self._itemtype3,
                                          amount_available=2,
                                          amount_measure=self._measure,
                                          location=self._location,
                                          added_by=self._janeDoe)
        self._item4 = Item.objects.create(name="Item4",
                                          identifier="I4",
                                          description="Not complicated",
                                          item_type=self._itemtype3,
                                          amount_available=0,
                                          amount_measure=self._measure,
                                          location=self._location,
                                          added_by=self._janeDoe)

        # Joe can see and edit items 1+2, and see item 3 but not edit it. No access to 4.
        # Jane can see and edit items 3+4, and see items 1+2 but not edit them.
        ViewPermissionsMixin().assign_permissions(instance=self._item1,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._item2,
                                                  permissions={"joe_group": "rw",
                                                               "jane_group": "r"})
        ViewPermissionsMixin().assign_permissions(instance=self._item3,
                                                  permissions={"joe_group": "r",
                                                               "jane_group": "rw"})
        ViewPermissionsMixin().assign_permissions(instance=self._item4,
                                                  permissions={"jane_group": "rw"})

        # We also have to give Joe and Jane permission to view, change and delete items in
        # general.
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="add_item"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="view_item"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="change_item"))
        self._joeBloggs.user_permissions.add(
            Permission.objects.get(codename="delete_item"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="add_item"))
        self._janeDoe.user_permissions.add(Permission.objects.get(codename="view_item"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="change_item"))
        self._janeDoe.user_permissions.add(
            Permission.objects.get(codename="delete_item"))

    def test_presets(self):
        self.assertEqual(Item.objects.count(), 4)
        i = Item.objects.get(name="Item1")
        self.assertEqual(i.name, "Item1")
        self.assertEqual(i.identifier, "I1")
        self.assertEqual(i.description, "Complicated")
        self.assertEqual(i.item_type, self._itemtype1)
        self.assertIs(i.in_inventory, True)
        self.assertEqual(i.amount_available, 5)
        self.assertEqual(i.amount_measure, self._measure)
        self.assertEqual(i.location, self._location2)
        self.assertEqual(i.added_by, self._joeBloggs)
        i = Item.objects.get(name="Item2")
        self.assertEqual(i.name, "Item2")
        self.assertEqual(i.identifier, "I2")
        self.assertEqual(i.description, "Even more complicated")
        self.assertEqual(i.item_type, self._itemtype2)
        self.assertIs(i.in_inventory, True)
        self.assertEqual(i.amount_available, 3)
        self.assertEqual(i.amount_measure, self._measure)
        self.assertEqual(i.concentration, 0.5)
        self.assertEqual(i.concentration_measure, self._measure3)
        self.assertEqual(i.location, self._location)
        self.assertEqual(i.added_by, self._joeBloggs)
        i = Item.objects.get(name="Item3")
        self.assertEqual(i.name, "Item3")
        self.assertEqual(i.identifier, "I3")
        self.assertEqual(i.description, "Less complicated")
        self.assertEqual(i.item_type, self._itemtype3)
        self.assertIs(i.in_inventory, True)
        self.assertEqual(i.amount_available, 2)
        self.assertEqual(i.amount_measure, self._measure)
        self.assertEqual(i.location, self._location)
        self.assertEqual(i.added_by, self._janeDoe)
        i = Item.objects.get(name="Item4")
        self.assertEqual(i.name, "Item4")
        self.assertEqual(i.identifier, "I4")
        self.assertEqual(i.description, "Not complicated")
        self.assertEqual(i.item_type, self._itemtype3)
        self.assertIs(i.in_inventory, False)
        self.assertEqual(i.amount_available, 0)
        self.assertEqual(i.amount_measure, self._measure)
        self.assertEqual(i.location, self._location)
        self.assertEqual(i.added_by, self._janeDoe)

    def test_access_anonymous(self):
        self._asAnonymous()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/inventory/%d/' % self._item1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_invalid(self):
        self._asInvalid()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/inventory/%d/' % self._item1.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list(self):
        # Joe can only see items his group can see
        self._asJoeBloggs()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 3)
        i = items["results"][0]
        self.assertEqual(i["name"], "Item1")

    def test_user_list_group(self):
        # Jane can see all four because her group permissions permit this
        self._asJaneDoe()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 4)

    def test_user_view_own(self):
        self._asJoeBloggs()
        response = self._client.get('/inventory/%d/' % self._item1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = response.data
        self.assertEqual(i["name"], "Item1")

    def test_user_view_other(self):
        # Jane's item 4 is only visible for Jane's group
        self._asJoeBloggs()
        response = self._client.get('/inventory/%d/' % self._item4.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_view_group(self):
        # Jane's group has read access to Joe's items 1+2
        self._asJaneDoe()
        response = self._client.get('/inventory/%d/' % self._item1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = response.data
        self.assertEqual(i["name"], "Item1")

    def test_admin_list(self):
        self._asAdmin()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 4)

    def test_admin_view_any(self):
        self._asAdmin()
        response = self._client.get('/inventory/%d/' % self._item2.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = response.data
        self.assertEqual(i["name"], "Item2")

    def test_user_create_own(self):
        self._asJaneDoe()
        new_item = {"name": "Item5",
                    "identifier": "I5",
                    "description": "Extremely complicated",
                    "item_type": self._itemtype3.name,
                    "amount_available": 5,
                    "amount_measure": self._measure.symbol,
                    "location": self._location.code,
                    "added_by": self._janeDoe.id,
                    "properties": [{"name": "joe", "value": "bloggs"}],
                    "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/inventory/", new_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Item.objects.count(), 5)
        self.assertIs(Item.objects.filter(name="Item5").exists(), True)
        i = Item.objects.get(identifier="I5")
        self.assertEqual(i.added_by, self._janeDoe)
        self.assertIs(i.properties.filter(name="joe").exists(), True)
        self.assertEqual(i.properties.get(name="joe").value, "bloggs")

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 3)
        self._asJaneDoe()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 5)

    def test_admin_create_any(self):
        # Admin should be able to create a set for someone else
        self._asAdmin()
        new_item = {"name": "Item5",
                    "identifier": "I5",
                    "description": "Extremely complicated",
                    "item_type": self._itemtype1.name,
                    "amount_available": 5,
                    "amount_measure": self._measure.symbol,
                    "location": self._location.code,
                    "properties": [{"name": "joe", "value": "bloggs"}],
                    "assign_groups": {"jane_group": "rw"}}
        response = self._client.post("/inventory/", new_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Item.objects.count(), 5)
        self.assertIs(Item.objects.filter(name="Item5").exists(), True)
        i = Item.objects.get(identifier="I5")
        self.assertEqual(i.added_by, self._adminUser)
        self.assertIs(i.properties.filter(name="joe").exists(), True)
        self.assertEqual(i.properties.get(name="joe").value, "bloggs")

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 3)
        self._asJaneDoe()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 5)

    def test_user_edit_own(self):
        self._asJoeBloggs()
        updated_item = {"description": "Blah",
                        "properties": [{"name": "joe", "value": "bloggs"}]}
        response = self._client.patch("/inventory/%d/" % self._item1.id,
                                      updated_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(i.description, "Blah")
        self.assertIs(i.properties.filter(name="joe").exists(), True)
        self.assertEqual(i.properties.get(name="joe").value, "bloggs")

    def test_user_edit_other_nonread(self):
        # Joe cannot see Jane's item 4
        self._asJoeBloggs()
        updated_item = {"description": "Blah",
                        "properties": [{"name": "joe", "value": "bloggs"}]}
        response = self._client.patch("/inventory/%d/" % self._item4.id,
                                      updated_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        i = Item.objects.get(name="Item4")
        self.assertEqual(i.description, "Not complicated")

    def test_user_edit_other_readonly(self):
        # Joe can see but not edit Jane's item 3
        self._asJoeBloggs()
        updated_item = {"description": "Blah",
                        "properties": [{"name": "joe", "value": "bloggs"}]}
        response = self._client.patch("/inventory/%d/" % self._item3.id,
                                      updated_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        i = Item.objects.get(name="Item3")
        self.assertEqual(i.description, "Less complicated")

    def test_user_edit_other_readwrite(self):
        # Give Jane write permission to Joe's item 1 first so she can edit it
        ViewPermissionsMixin().assign_permissions(instance=self._item1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        updated_item = {"description": "Blah",
                        "properties": [{"name": "joe", "value": "bloggs"}]}
        response = self._client.patch("/inventory/%d/" % self._item1.id,
                                      updated_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(i.description, "Blah")
        self.assertIs(i.properties.filter(name="joe").exists(), True)
        self.assertEqual(i.properties.get(name="joe").value, "bloggs")

    def test_admin_edit_any(self):
        self._asAdmin()
        updated_item = {"description": "Blah",
                        "properties": [{"name": "joe", "value": "bloggs"}]}
        response = self._client.patch("/inventory/%d/" % self._item1.id,
                                      updated_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(i.description, "Blah")
        self.assertIs(i.properties.filter(name="joe").exists(), True)
        self.assertEqual(i.properties.get(name="joe").value, "bloggs")

    def test_admin_add_remove_properties(self):
        self._asAdmin()
        updated_item = {"properties": [{"name": "joe", "value": "bloggs"},
                                       {"name": "jim", "value": "beam"}]}
        response = self._client.patch("/inventory/%d/" % self._item1.id,
                                      updated_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertIs(i.properties.filter(name="joe").exists(), True)
        self.assertEqual(i.properties.get(name="joe").value, "bloggs")
        self.assertIs(i.properties.filter(name="jim").exists(), True)
        self.assertEqual(i.properties.get(name="jim").value, "beam")
        updated_item = {"properties": [{"name": "jane", "value": "doe"},
                                       {"name": "jim", "value": "jones"}]}
        response = self._client.patch("/inventory/%d/" % self._item1.id,
                                      updated_item, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertIs(i.properties.filter(name="joe").exists(), False)
        self.assertIs(i.properties.filter(name="jane").exists(), True)
        self.assertEqual(i.properties.get(name="jane").value, "doe")
        self.assertIs(i.properties.filter(name="jim").exists(), True)
        self.assertEqual(i.properties.get(name="jim").value, "jones")

    def test_user_delete_own(self):
        self._asJaneDoe()
        response = self._client.delete("/inventory/%d/" % self._item3.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Item.objects.filter(name="Item3").exists(), False)

    def test_user_delete_other_noread(self):
        # Joe can only see/edit his
        self._asJoeBloggs()
        response = self._client.delete("/inventory/%d/" % self._item4.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(Item.objects.filter(name="Item4").exists(), True)

    def test_user_delete_other_readonly(self):
        # Jane can edit hers and see both
        self._asJaneDoe()
        response = self._client.delete("/inventory/%d/" % self._item2.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIs(Item.objects.filter(name="Item2").exists(), True)

    def test_user_delete_other_readwrite(self):
        # Give Jane write permission to Joe's group first so she can delete it
        ViewPermissionsMixin().assign_permissions(instance=self._item1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete("/inventory/%d/" % self._item1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Item.objects.filter(name="Item1").exists(), False)

    def test_admin_delete_any(self):
        self._asAdmin()
        response = self._client.delete("/inventory/%d/" % self._item1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIs(Item.objects.filter(name="Item1").exists(), False)

    def test_user_set_permissions_own(self):
        # Any user should be able to set permissions on own sets
        self._asJoeBloggs()
        permissions = {"joe_group": "rw", "jane_group": "rw"}
        response = self._client.patch(
            "/inventory/%d/set_permissions/" % self._item1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_nonread(self):
        # Joe is not in the right group to see Jane's project
        self._asJoeBloggs()
        permissions = {"jane_group": "r"}
        response = self._client.patch(
            "/inventory/%d/set_permissions/" % self._item4.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        i = Item.objects.get(name="Item4")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_set_permissions_readonly(self):
        # Jane can see but not edit Joe's project
        self._asJaneDoe()
        permissions = {"jane_group": "rw"}
        response = self._client.patch(
            "/inventory/%d/set_permissions/" % self._item1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_set_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._item1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/inventory/%d/set_permissions/" % self._item1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_admin_set_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        permissions = {"joe_group": "r", "jane_group": "r"}
        response = self._client.patch(
            "/inventory/%d/set_permissions/" % self._item1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "r")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_set_permissions_invalid_group(self):
        # An invalid group should throw a 400 data error
        self._asAdmin()
        permissions = {"jim_group": "r"}
        response = self._client.patch(
            "/inventory/%d/set_permissions/" % self._item1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the group wasn't created accidentally in the process
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_set_permissions_invalid_permission(self):
        # An invalid permission should throw a 400 data error
        self._asAdmin()
        permissions = {"joe_group": "flibble"}
        response = self._client.patch(
            "/inventory/%d/set_permissions/" % self._item1.id,
            permissions, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check the permission wasn't changed accidentally in the process
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

    def test_user_remove_permissions_own(self):
        # Any user should be able to remove permissions on own projects
        self._asJoeBloggs()
        response = self._client.delete(
            "/inventory/%d/remove_permissions/?groups=joe_group" % self._item1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_user_remove_permissions_nonread(self):
        # Joe is not in the right group to see Jane's item 4
        self._asJoeBloggs()
        response = self._client.delete(
            "/inventory/%d/remove_permissions/?groups=jane_group" % self._item4.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        i = Item.objects.get(name="Item4")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "rw")

    def test_user_remove_permissions_readonly(self):
        # Jane can see but not edit Joe's item 1
        self._asJaneDoe()
        response = self._client.delete(
            "/inventory/%d/remove_permissions/?groups=joe_group" % self._item1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")

    def test_user_remove_permissions_readwrite(self):
        # Jane can see and edit Joe's project if we change her permissions first
        ViewPermissionsMixin().assign_permissions(instance=self._item1,
                                                  permissions={"jane_group": "rw"})
        self._asJaneDoe()
        response = self._client.delete(
            "/inventory/%d/remove_permissions/?groups=joe_group" % self._item1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_admin_remove_permissions(self):
        # Admin can do what they like
        self._asAdmin()
        response = self._client.delete(
            "/inventory/%d/remove_permissions/?groups=jane_group&groups=joe_group" %
            self._item1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i = Item.objects.get(name="Item1")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), None)
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), None)

    def test_remove_permissions_invalid_group(self):
        # An invalid group name should fail quietly - we don't care if permissions can't be
        # removed as the end result is the same, i.e. that group can't access anything
        self._asAdmin()
        response = self._client.delete(
            "/inventory/%d/remove_permissions/?groups=jim_group" %
            self._item1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that the group wasn't created accidentally
        self.assertIs(Group.objects.filter(name="jim_group").exists(), False)

    def test_transfer_user_add(self):
        self._asJoeBloggs()
        new_transfer = {"amount": 100,
                        "measure": "ml",
                        "is_addition": True}
        response = self._client.post(
            "/inventory/%d/transfer/" %
            self._item1.id, new_transfer,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i1 = Item.objects.get(name="Item1")
        self.assertEqual(i1.amount_available, 5.1)
        transfers = i1.transfers
        self.assertEqual(transfers.count(), 1)
        transfer = transfers.all()[0]
        self.assertIs(transfer.is_addition, True)
        self.assertIs(transfer.transfer_complete, True)
        self.assertEqual(response.data["message"], 'Transfer {} created'.format(transfer.id))

    def test_transfer_admin_add(self):
        self._asAdmin()
        new_transfer = {"amount": 100,
                        "measure": "ml",
                        "is_addition": True}
        response = self._client.post(
            "/inventory/%d/transfer/" %
            self._item1.id, new_transfer,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i1 = Item.objects.get(name="Item1")
        self.assertEqual(i1.amount_available, 5.1)
        transfers = i1.transfers
        self.assertEqual(transfers.count(), 1)
        transfer = transfers.all()[0]
        self.assertIs(transfer.is_addition, True)
        self.assertIs(transfer.transfer_complete, True)
        self.assertEqual(response.data["message"], 'Transfer {} created'.format(transfer.id))

    def test_transfer_user_remove_then_complete(self):
        self._asJoeBloggs()
        new_transfer = {"amount": 100,
                        "measure": "ml"}
        response = self._client.post(
            "/inventory/%d/transfer/" %
            self._item1.id, new_transfer,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i1 = Item.objects.get(name="Item1")
        self.assertEqual(i1.amount_available, 4.9)
        transfers = i1.transfers
        self.assertEqual(transfers.count(), 1)
        transfer = transfers.all()[0]
        self.assertIs(transfer.is_addition, False)
        self.assertIs(transfer.transfer_complete, False)
        self.assertEqual(response.data["message"], 'Transfer {} created'.format(transfer.id))

        response = self._client.post(
            "/inventory/%d/transfer/?id=%d&complete=True" %
            (self._item1.id, transfer.id),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i1 = Item.objects.get(name="Item1")
        transfers = i1.transfers
        transfer = transfers.all()[0]
        self.assertIs(transfer.is_addition, False)
        self.assertIs(transfer.transfer_complete, True)
        self.assertEqual(response.data["message"], 'Transfer {} complete'.format(transfer.id))

    def test_transfer_admin_remove_then_complete(self):
        self._asAdmin()
        new_transfer = {"amount": 100,
                        "measure": "ml"}
        response = self._client.post(
            "/inventory/%d/transfer/" %
            self._item1.id, new_transfer,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i1 = Item.objects.get(name="Item1")
        self.assertEqual(i1.amount_available, 4.9)
        transfers = i1.transfers
        self.assertEqual(transfers.count(), 1)
        transfer = transfers.all()[0]
        self.assertIs(transfer.is_addition, False)
        self.assertIs(transfer.transfer_complete, False)
        self.assertEqual(response.data["message"], 'Transfer {} created'.format(transfer.id))

        response = self._client.post(
            "/inventory/%d/transfer/?id=%d&complete=True" %
            (self._item1.id, transfer.id),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        i1 = Item.objects.get(name="Item1")
        transfers = i1.transfers
        transfer = transfers.all()[0]
        self.assertIs(transfer.is_addition, False)
        self.assertIs(transfer.transfer_complete, True)
        self.assertEqual(response.data["message"], 'Transfer {} complete'.format(transfer.id))

    def test_transfer_remove_notenough(self):
        self._asJoeBloggs()
        new_transfer = {"amount": 100,
                        "measure": "l"}
        response = self._client.post(
            "/inventory/%d/transfer/" %
            self._item1.id, new_transfer,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        i1 = Item.objects.get(name="Item1")
        self.assertEqual(response.data["message"],
                         'Inventory item {} ({}) is short of amount by {} liter'.format(
                             i1.identifier, i1.name, 95.0))
        self.assertEqual(i1.amount_available, 5)
        transfers = i1.transfers.all()
        self.assertEqual(len(transfers), 0)

    def test_transfer_complete_missing_id(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/inventory/%d/transfer/?complete=True" %
            self._item1.id,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], 'You must provide a transfer ID')

    def test_transfer_complete_invalid_id(self):
        self._asJoeBloggs()
        response = self._client.post(
            "/inventory/%d/transfer/?id=%d&complete=True" %
            (self._item1.id, 99999),
            format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], 'No item transfer exists with that ID')

    def test_transfer_invalid_unit(self):
        # Should throw an error
        self._asJoeBloggs()
        new_transfer = {"amount": 1,
                        "measure": "blobby"}
        response = self._client.post(
            "/inventory/%d/transfer/" %
            self._item1.id, new_transfer,
            format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], 'Measure blobby does not exist')

    def test_importitems(self):
        self._asJoeBloggs()

        templ = FileTemplate.objects.create(name="ItemTemplate",
                                            file_for="input")
        FileTemplateField.objects.create(name="name",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)
        FileTemplateField.objects.create(name="identifier",
                                         required=True,
                                         is_identifier=True,
                                         template=templ)
        FileTemplateField.objects.create(name="description",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)
        FileTemplateField.objects.create(name="item_type",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)
        FileTemplateField.objects.create(name="amount_available",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)
        FileTemplateField.objects.create(name="amount_measure",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)
        FileTemplateField.objects.create(name="location",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)
        FileTemplateField.objects.create(name="properties",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)

        filename = 'test.csv'
        file = open(filename, 'w')
        templ.write(file, [
            {
                "name": "Item5",
                "identifier": "I5",
                "description": "Extremely complicated",
                "item_type": self._itemtype1.name,
                "amount_available": 5,
                "amount_measure": self._measure.symbol,
                "location": self._location.code,
                "properties": [{"name": "joe", "value": "bloggs"},
                               {"name": "jane", "value": "doe"}]},
            {
                "name": "Item6",
                "identifier": "I6",
                "description": "Moderately complicated",
                "item_type": self._itemtype2.name,
                "amount_available": 15,
                "amount_measure": self._measure.symbol,
                "location": self._location.code,
                "properties": [{"name": "jim", "value": "beam"}]
            },
            {
                "name": "Item7",
                "identifier": "I7",
                "description": "INVALID",
            }], "name")
        file.close()
        with open(filename) as fp:
            response = self._client.post(
                "/inventory/importitems/", {"filetemplate": templ.id,
                                            "items_file": fp,
                                            "permissions": {"joe_group": "rw", "jane_group": "r"}},
                format='json')
        os.remove(filename)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs("saved" in response.data, True)
        self.assertIs("rejected" in response.data, True)
        saved = response.data["saved"]
        rejected = response.data["rejected"]
        self.assertEqual(len(saved), 2)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["identifier"], "I7")
        self.assertIsNotNone(rejected[0]["errors"])

        self.assertEqual(Item.objects.count(), 6)
        self.assertIs(Item.objects.filter(name="Item5").exists(), True)
        i = Item.objects.get(identifier="I5")
        self.assertEqual(i.added_by, self._joeBloggs)
        self.assertIs(i.properties.filter(name="joe").exists(), True)
        self.assertEqual(i.properties.get(name="joe").value, "bloggs")
        self.assertIs(i.properties.filter(name="jane").exists(), True)
        self.assertEqual(i.properties.get(name="jane").value, "doe")
        self.assertEqual(i.description, "Extremely complicated")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")
        self.assertIs(Item.objects.filter(name="Item6").exists(), True)
        i = Item.objects.get(identifier="I6")
        self.assertEqual(i.added_by, self._joeBloggs)
        self.assertIs(i.properties.filter(name="jim").exists(), True)
        self.assertEqual(i.properties.get(name="jim").value, "beam")
        self.assertEqual(i.description, "Moderately complicated")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="joe_group")), "rw")
        self.assertEqual(
            ViewPermissionsMixin().current_permissions(instance=i,
                                                       group=Group.objects.get(
                                                           name="jane_group")), "r")

        # Other user still sees just theirs but we see both our old and new ones plus those we
        # have group access to
        self._asJoeBloggs()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 5)
        self._asJaneDoe()
        response = self._client.get('/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data
        self.assertEqual(len(items["results"]), 6)

    def test_importitems_invalid_template(self):
        self._asJoeBloggs()

        filename = "test.csv"
        file = open(filename, "w")
        file.write("blah,blah,blah")
        file.close()
        with open(filename) as fp:
            response = self._client.post(
                "/inventory/importitems/",
                {"filetemplate": 99999,
                 "items_file": fp,
                 "permissions": {"joe_group": "rw", "jane_group": "r"}},
                format='json')
        os.remove(filename)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "File template does not exist")

    def test_importitems_invalid_format(self):
        self._asJoeBloggs()

        templ = FileTemplate.objects.create(name="ItemTemplate",
                                            file_for="input")
        FileTemplateField.objects.create(name="name",
                                         required=True,
                                         is_identifier=False,
                                         template=templ)

        filename = "test.csv"
        file = open(filename, "w")
        file.write("All rubbish\nShould never work\nBut, it might!")
        file.close()
        with open(filename) as fp:
            response = self._client.post(
                "/inventory/importitems/", {"filetemplate": templ.id,
                                            "items_file": fp,
                                            "permissions": {"joe_group": "rw", "jane_group": "r"}},
                format='json')
        os.remove(filename)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "File is format is incorrect")

    def test_item_get_tags(self):
        self.assertEqual(self._item1.get_tags(), "hello, world")

    def test_item_location_path(self):
        self.assertEqual(self._item1.location_path(), "On top of the cupboard > On a shelf")
