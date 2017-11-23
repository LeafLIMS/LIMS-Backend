from django.db import models
import reversion

from lims.shared.models import Organism


@reversion.register()
class CodonUsageTable(models.Model):
    species = models.ForeignKey(Organism)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.species.name


@reversion.register()
class CodonUsage(models.Model):
    name = models.CharField(max_length=3)
    value = models.FloatField()

    table = models.ForeignKey(CodonUsageTable, related_name='codons')

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return '{}/{}'.format(self.table, self.name)
