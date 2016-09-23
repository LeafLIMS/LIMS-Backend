from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import Organism


class SharedTestCase(LoggedInTestCase):
    def setUp(self):
        super(SharedTestCase, self).setUp()

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
