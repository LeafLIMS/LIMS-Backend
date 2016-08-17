from lims.shared.loggedintestcase import LoggedInTestCase
from rest_framework import status
from .models import CodonUsage, CodonUsageTable, Organism


class CodonUsageTestCase(LoggedInTestCase):
    def setUp(self):
        super(CodonUsageTestCase, self).setUp()
        # These objects are recreated afresh for every test method below.
        # Data updated or created in a test method will not persist to another test method.
        self._human = Organism.objects.create(name="Homo sapiens", common_name="Human")
        self._cow = Organism.objects.create(name="Bos taurus", common_name="Cow")
        self._mouse = Organism.objects.create(name="Mus musculus", common_name="Mouse")

        self._human_codontable = CodonUsageTable.objects.create(species=self._human)
        self._human_codon1 = CodonUsage.objects.create(name="GAT", value=0.1, table=self._human_codontable)
        self._human_codon2 = CodonUsage.objects.create(name="GCT", value=0.02, table=self._human_codontable)

        self._cow_codontable = CodonUsageTable.objects.create(species=self._cow)
        self._cow_codon1 = CodonUsage.objects.create(name="CAG", value=0.03, table=self._cow_codontable)
        self._cow_codon2 = CodonUsage.objects.create(name="CCA", value=0.45, table=self._cow_codontable)

    # Preset codons from the constructor should return the values they were given
    def test_001_db_preset_codontables_correct(self):
        # Check organisms (species)
        self.assertIs(Organism.objects.filter(name="Homo sapiens").exists(), True)
        organism1 = Organism.objects.get(name="Homo sapiens")
        self.assertEqual(organism1.common_name, "Human")
        self.assertIs(Organism.objects.filter(name="Bos taurus").exists(), True)
        organism2 = Organism.objects.get(name="Bos taurus")
        self.assertEqual(organism2.common_name, "Cow")
        # Check codon table for human
        self.assertIs(CodonUsageTable.objects.filter(species=organism1).exists(), True)
        codontable1 = CodonUsageTable.objects.get(species=organism1).codons.all()
        self.assertEqual(len(codontable1), 2)
        codon1_1 = codontable1[0]
        self.assertEqual(codon1_1.name, "GAT")
        self.assertEqual(codon1_1.value, 0.1)
        codon1_2 = codontable1[1]
        self.assertEqual(codon1_2.name, "GCT")
        self.assertEqual(codon1_2.value, 0.02)
        # Check codon table for cow
        self.assertIs(CodonUsageTable.objects.filter(species=organism2).exists(), True)
        codontable2 = CodonUsageTable.objects.get(species=organism2).codons.all()
        self.assertEqual(len(codontable2), 2)
        codon2_1 = codontable2[0]
        self.assertEqual(codon2_1.name, "CAG")
        self.assertEqual(codon2_1.value, 0.03)
        codon2_2 = codontable2[1]
        self.assertEqual(codon2_2.name, "CCA")
        self.assertEqual(codon2_2.value, 0.45)

    # Anonymous users or users with invalid credentials cannot see anything
    def test_002_rest_no_anonymous_or_invalid_access(self):
        self._asAnonymous()
        response = self._client.get('/codonusage/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/codonusage/%d/' % self._human_codontable.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/codonusage/%d/codons/' % self._human_codontable.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self._asInvalid()
        response = self._client.get('/codonusage/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/codonusage/%d/' % self._human_codontable.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self._client.get('/codonusage/%d/codons/' % self._human_codontable.id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Users see all codon tables and codons
    def test_003_rest_all_codontable_content(self):
        self._asJoeBloggs()
        response = self._client.get('/codonusage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codontables = response.data
        self.assertEqual(len(codontables["results"]), 2)

    # Users can see a single codon table requested by table ID
    def test_004_rest_single_codontable_content(self):
        self._asJaneDoe()
        response = self._client.get('/codonusage/%d/' % self._cow_codontable.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codontable1 = response.data
        self.assertEqual(codontable1["species"], "Bos taurus")

    # Users can see a single codon table's contents requested by table ID
    def test_005_rest_single_codontable_content(self):
        self._asJaneDoe()
        response = self._client.get('/codonusage/%d/codons/' % self._cow_codontable.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codons1 = response.data
        self.assertEqual(len(codons1), 2)
        codon1 = codons1[0]
        self.assertEqual(codon1["name"], self._cow_codon1.name)
        self.assertEqual(codon1["value"], self._cow_codon1.value)
        codon2 = codons1[1]
        self.assertEqual(codon2["name"], self._cow_codon2.name)
        self.assertEqual(codon2["value"], self._cow_codon2.value)

    # Users cannot add an extra table of their own - service is read-only
    def test_006_rest_create_codontable(self):
        # Create a new address of our own
        self._asJaneDoe()
        new_codontable = {"species": self._mouse.id,
                          "codons": { "name": "AGT",
                                      "value": 1.34}
                          }
        response = self._client.post("/codonusage/", new_codontable, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # The DB should still only have 2 codon tables
        self.assertEqual(CodonUsageTable.objects.count(), 2)

    # Editing an existing codon table should fail - service is read-only
    def test_007_rest_update_codontable(self):
        self._asJoeBloggs()
        updated_codontable = {"species": self._mouse.id}
        response = self._client.patch("/codonusage/%d/" % self._human_codontable.id,
                                      updated_codontable, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Check edit really wasn't made
        self.assertIs(CodonUsageTable.objects.filter(species=self._human).exists(), True)
        self.assertIs(CodonUsageTable.objects.filter(species=self._mouse).exists(), False)

    # Deleting a table should fail - service is read-only
    def test_008_rest_delete_codontable(self):
        self._asJoeBloggs()
        response = self._client.delete("/codonusage/%d/" % self._cow_codontable.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Test the table still exists
        self.assertIs(CodonUsageTable.objects.filter(species=self._cow).exists(), True)
