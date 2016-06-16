from django.db import models

class Organism(models.Model):
    """
    Basic information on an Organism
    """
    name = models.CharField(max_length=100)
    common_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class LimsPermission(models.Model):
    """
    Allow access to the LIMS system
    """
    class Meta:
        permissions = (
            ('lims_access', 'Access LIMS system',),
        )
