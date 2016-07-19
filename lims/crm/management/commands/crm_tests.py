
from django.core.management.base import BaseCommand
from django.conf import settings

from simple_salesforce import Salesforce


class Command(BaseCommand):
    help = 'Imports a CSV of items into a inventory'

    def handle(self, *args, **options):
        sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                        username=settings.SALESFORCE_USERNAME,
                        password=settings.SALESFORCE_PASSWORD,
                        security_token=settings.SALESFORCE_TOKEN)

        ac = sf.Account.get('00124000003udGz')
        self.stdout.write(ac)
