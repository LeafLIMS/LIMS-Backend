from django.db import models
from django.contrib.auth.models import User


class Address(models.Model):
    institution_name = models.CharField(max_length=200)
    address_1 = models.CharField(max_length=100)
    address_2 = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10)
    country = models.CharField(max_length=100)

    user = models.ForeignKey(User, related_name='addresses')

    def __str__(self):
        return '{}: {}'.format(self.user.username, self.institution_name)
