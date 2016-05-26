from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from simple_salesforce import Salesforce

from lims.pricebook.models import PriceBook, Price

def get_pricebooks():
    sf = Salesforce(instance_url=settings.SALESFORCE_URL,
            username=settings.SALESFORCE_USERNAME,
            password=settings.SALESFORCE_PASSWORD,
            security_token=settings.SALESFORCE_TOKEN)

    pricebooks = PriceBook.objects.all()
    for pb in pricebooks:
        pricebook = sf.Pricebook2.get(pb.identifier)
        query = "SELECT Id,Name,ProductCode,UnitPrice,IsActive FROM PricebookEntry WHERE Pricebook2Id = '{}'".format(pb.identifier)
        remote_prices = sf.query(query)

        price_list, created = PriceBook.objects.get_or_create(name=pricebook['Name']) 

        for item in remote_prices['records']:
            price, created = Price.objects.get_or_create(code=item['ProductCode'],
                    defaults={
                        'name': item['Name'], 
                        'price': item['UnitPrice'],
                        'identifier': item['Id'] 
                        })
            price.name = item['Name']
            price.price = item['UnitPrice']
            price.identifier = item['Id'] 
            price.save()

            price_list.prices.add(price)

class Command(BaseCommand):
    help = 'Updates the customer portal price list from SalesForce'

    def handle(self, *args, **options):
        get_pricebooks()

