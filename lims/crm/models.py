from django.db import models
import reversion
from django.contrib.auth.models import User
from django.conf import settings

from lims.orders.models import Order


@reversion.register()
class CRMAccount(models.Model):
    contact_identifier = models.CharField(max_length=50)
    account_identifier = models.CharField(max_length=50, null=True, blank=True)

    account_name = models.CharField(max_length=200)

    user = models.OneToOneField(User)

    class Meta:
        permissions = (
            ('view_crmaccount', 'View CRM Account',),
        )

    def contact_url(self):
        return settings.SALESFORCE_URL + '/' + self.contact_identifier

    def account_url(self):
        if self.account_identifier:
            return settings.SALESFORCE_URL + '/' + self.account_identifier
        return ''

    def __str__(self):
        return self.user.username


@reversion.register()
class CRMProject(models.Model):
    project_identifier = models.CharField(max_length=50)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(blank=True, default='', max_length=100)

    account = models.ForeignKey(CRMAccount)

    # This should be on ORDER not CRM Project
    order = models.OneToOneField(Order, related_name='crm', null=True, blank=True)

    class Meta:
        permissions = (
            ('view_crmproject', 'View CRM Project',),
        )

    def project_url(self):
        return settings.SALESFORCE_URL + '/' + self.project_identifier

    def __str__(self):
        return self.name


@reversion.register()
class CRMQuote(models.Model):
    quote_identifier = models.CharField(max_length=50)

    quote_number = models.CharField(max_length=10)
    quote_name = models.CharField(max_length=200)
    subtotal = models.FloatField()
    discount = models.FloatField(null=True, blank=True)
    total = models.FloatField()

    project = models.ForeignKey(CRMProject, related_name='quotes')

    class Meta:
        permissions = (
            ('view_crmquote', 'View CRM Quote',),
        )

    def quote_url(self):
        return settings.SALESFORCE_URL + '/' + self.quote_identifier

    def __str__(self):
        return self.quote_name
