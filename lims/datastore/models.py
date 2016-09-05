from django.db import models

from lims.equipment.models import Equipment


class DataFile(models.Model):
    """
    Metadata describing a file extracted from a piece of equipment

    Any parsed data will then be applied directly to the
    corosponding DataEntry object attached to a Product.
    """
    file_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    run_identifier = models.CharField(max_length=64)
    date_created = models.DateTimeField(auto_now_add=True)
    equipment = models.ForeignKey(Equipment)
