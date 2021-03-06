from django.db import models
import reversion
from django.contrib.auth.models import User

from django.contrib.postgres.fields import JSONField

from lims.equipment.models import Equipment


@reversion.register()
class DataFile(models.Model):
    """
    Metadata describing a file extracted from a piece of equipment

    Any parsed data will then be applied directly to the
    corosponding DataEntry object attached to a Product.
    """
    file_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    date_created = models.DateTimeField(auto_now_add=True)
    equipment = models.ForeignKey(Equipment)


@reversion.register()
class DataEntry(models.Model):

    STATE = (
        ('active', 'In Progress'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('repeat succeeded', 'Repeat succeeded'),
        ('repeat failed', 'Repeat Failed'),
    )

    run = models.ForeignKey('workflows.Run',
                            null=True,
                            related_name='data_entries')
    # Unique identifier for the task/run combo
    task_run_identifier = models.UUIDField(db_index=True)

    product = models.ForeignKey('projects.Product', related_name='data')
    item = models.ForeignKey('inventory.Item', null=True, related_name='data_entries')
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User)
    state = models.CharField(max_length=20, choices=STATE)
    # Any information on things such as reasons for failure etc.
    notes = models.TextField(blank=True, null=True)
    data = JSONField()
    data_files = models.ManyToManyField(DataFile, blank=True)

    task = models.ForeignKey('workflows.TaskTemplate')

    def product_name(self):
        return '{} {}'.format(self.product.product_identifier, self.product.name)

    def __str__(self):
        return '{}: {}'.format(self.date_created, self.task)

    class Meta:
        ordering = ['-date_created']


@reversion.register()
class Attachment(models.Model):
    """
    A file stored on the system and linked to one or more items
    """
    attachment = models.FileField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User)

    def attachment_name(self):
        return self.attachment.name.split('/')[-1]
