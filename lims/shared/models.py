from django.db import models

class Organism(models.Model):
    """
    Basic information on an Organism
    """
    name = models.CharField(max_length=100)
    common_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

