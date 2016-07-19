from django.db import models


class Price(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    price = models.FloatField()
    identifier = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class PriceBook(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    description = models.TextField(null=True, blank=True)
    identifier = models.CharField(max_length=20, null=True)

    prices = models.ManyToManyField(Price, blank=True)

    def __str__(self):
        return self.name
