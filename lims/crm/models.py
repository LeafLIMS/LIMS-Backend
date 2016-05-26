from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from lims.orders.models import Order

class CRMAccount(models.Model):
    contact_identifier = models.CharField(max_length=50)
    account_identifier = models.CharField(max_length=50)

    user = models.OneToOneField(User)

    def __str__(self):
        return self.user.username

class CRMProject(models.Model):
    project_identifier = models.CharField(max_length=50)

    order = models.OneToOneField(Order, related_name='crm', null=True)

    def __str__(self):
        return self.order.name

class CRMQuote(models.Model):
    quote_identifier = models.CharField(max_length=50)

    quote_number = models.CharField(max_length=10)
    quote_name = models.CharField(max_length=200)
    subtotal = models.FloatField()
    discount = models.FloatField(null=True, blank=True)
    total = models.FloatField()

    project = models.ForeignKey(CRMProject, related_name='quotes')

    def quote_url(self):
        return settings.SALESFORCE_URL+'/'+self.quote_identifier 

    def __str__(self):
        return self.project.order.name + ': '+ self.quote_identifier
