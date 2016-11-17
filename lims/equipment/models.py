from django.db import models
import reversion
from django.contrib.auth.models import User
from django.contrib.postgres.fields import DateTimeRangeField
from django.utils import timezone

from psycopg2.extras import DateTimeTZRange

from lims.inventory.models import Location


@reversion.register()
class Equipment(models.Model):
    EQUIPMENT_STATUS_CHOICES = (
        ('active', 'Active',),
        ('idle', 'Idle',),
        ('error', 'Error',),
        ('broken', 'Out of order',),
    )

    name = models.CharField(max_length=50, unique=True)
    location = models.ForeignKey(Location)

    status = models.CharField(choices=EQUIPMENT_STATUS_CHOICES,
                              default='idle',
                              max_length=30)

    can_reserve = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def next_three_reservations(self):
        # Limit the number of reservations returned to three
        # as we really don't need all of them.
        now = timezone.now()
        return self.reservations.filter(start__gte=now).order_by('start')[:3]

    def __str__(self):
        return self.name


# @reversion.register()
class EquipmentReservation(models.Model):
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField(db_index=True)

    reservation = DateTimeRangeField(null=True)

    # The person for which the equipment is reserved for (they may not be
    # in the system i.e. if they are a PhD student
    reserved_for = models.CharField(max_length=200, null=True, blank=True)
    # The actual person who reserved the equipment (aka the person to ask
    # who they are)
    reserved_by = models.ForeignKey(User, related_name='reserved_by')
    equipment_reserved = models.ForeignKey(Equipment, related_name='reservations')

    is_confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(User, null=True, blank=True)

    checked_in = models.BooleanField(default=False)

    def full_user_name(self):
        return '{} {}'.format(self.reserved_by.first_name,
                              self.reserved_by.last_name)

    def __str__(self):
        return '{} reserved for {} from {} to {}'.format(
            self.equipment_reserved.name, self.title(),
            self.start, self.end)

    def save(self, *args, **kwargs):
        # Staff are automatically confirmed.
        if self.reserved_by.groups.filter(name='staff').exists():
            self.is_confirmed = True
            self.confirmed_by = self.reserved_by
        # Take the start and end dates to generate a timerange
        # to actually query on as solves issues just using start
        # and end dates.
        self.reservation = DateTimeTZRange(self.start, self.end)
        super(EquipmentReservation, self).save(*args, **kwargs)

    def title(self):
        return self.full_user_name()
