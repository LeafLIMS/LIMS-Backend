from django.db import models
import reversion


@reversion.register()
class Organism(models.Model):
    """
    Basic information on an Organism
    """
    name = models.CharField(max_length=100)
    common_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


@reversion.register()
class LimsPermission(models.Model):
    """
    Allow access to the LIMS system
    """
    class Meta:
        permissions = (
            ('lims_access', 'Access LIMS system',),
        )
