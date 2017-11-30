from django.db import models
import reversion


@reversion.register()
class Price(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    price = models.FloatField()
    identifier = models.CharField(max_length=20)

    def __str__(self):
        return self.name


@reversion.register()
class PriceBook(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    description = models.TextField(null=True, blank=True)
    identifier = models.CharField(max_length=20, null=True)

    prices = models.ManyToManyField(Price, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name
