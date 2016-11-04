from django.db import models
import reversion
from django.contrib.auth.models import User

from jsonfield import JSONField


@reversion.register()
class Service(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


@reversion.register()
class Order(models.Model):

    STATUS_BAR_CHOICES = (
        ('Submitted', 'Submitted'),
        ('Quote Sent', 'Quote Sent'),
        ('Order Received', 'Order Received'),
        ('Project in Progress', 'Project in Progress'),
        ('Project Shipped', 'Project Shipped'),
    )

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=100)
    services = models.ManyToManyField(Service)
    data = JSONField()
    status_bar_status = models.CharField(
        max_length=30, choices=STATUS_BAR_CHOICES, default="Submitted")

    user = models.ForeignKey(User)

    date_placed = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    is_quote = models.BooleanField(default=False)

    quote_sent = models.BooleanField(default=False)
    po_receieved = models.BooleanField(default=False, verbose_name='Purchase order receieved')
    po_reference = models.CharField(max_length=50, null=True, blank=True)
    invoice_sent = models.BooleanField(default=False)
    has_paid = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_updated']
