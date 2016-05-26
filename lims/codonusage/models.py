from django.db import models

from lims.shared.models import Organism

class CodonUsageTable(models.Model):
    species = models.ForeignKey(Organism) 

    def __str__(self):
        return self.species.name

class CodonUsage(models.Model):
    name = models.CharField(max_length=3)
    value = models.FloatField()

    table = models.ForeignKey(CodonUsageTable, related_name='codons')

    def __str__(self):
        return '{}/{}'.format(self.table, self.name)
