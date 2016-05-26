import datetime
import pytz

from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

from simple_salesforce import Salesforce
from django_countries import countries

from lims.users.serializers import UserSerializer
from lims.orders.models import Order
from lims.pricebook.models import Price, PriceBook
from .models import CRMAccount, CRMProject, CRMQuote

class CRMUserView(APIView):
    """
    Deals with the creation and upkeep of SalesForce account and
    contact information.
    """

    def post(self, request, format=None):
        """
        Adds the necessary account and contact data to Salesforce if they do not exist. 
        """

        sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                username=settings.SALESFORCE_USERNAME,
                password=settings.SALESFORCE_PASSWORD,
                security_token=settings.SALESFORCE_TOKEN)

        contact_id = ''
        account_id = ''

        contacts_query = "SELECT Id,AccountId,FirstName,LastName,Email FROM Contact WHERE Email = '{}'".format(
                request.data['email'])
        contacts = sf.query(contacts_query)
        if contacts['totalSize'] > 0:
            contact_id = contacts['records'][0]['Id']
            account_id = contacts['records'][0]['AccountId']
        else:
            account_query = "SELECT Id,Name FROM Account WHERE Name = '{}'".format(
                    request.data['institution_name'])
            accounts = sf.query(account_query)
            if accounts['totalSize'] == 0:
                result = sf.Account.create({'Name': request.data['institution_name']})
                account_id = result['id'];
            else:
                account_id = accounts['records'][0]['Id']

            country_codes = dict((value, key) for key, value in dict(countries).items())

            contact = sf.Contact.create({
                'FirstName': request.data['first_name'],
                'LastName': request.data['last_name'],
                'AccountId': account_id,
                'Email': request.data['email'],
                'MailingStreet': request.data['address_1'] + '\n ' + request.data.get('address_2', ''),
                'MailingCity': request.data['city'],
                'MailingPostalCode': request.data['postcode'],
                'MailingCountryCode': country_codes[request.data['country']], 
            })
            contact_id = contact['id']

        if contact_id and account_id:
            user = User.objects.get(username=request.data['email'])

            details = CRMAccount(contact_identifier=contact_id,
                    account_identifier=account_id,
                    user=user)
            details.save()

            user = User.objects.get(username=request.data['email'])

            s = UserSerializer(user)
            return Response(s.data)
        return Response({'No CRM data added to account'})

class CRMProjectView(APIView):

    def post(self, request, format=None):
        """
        Adds a project to Salesforce and creates references on system.
        """
        sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                username=settings.SALESFORCE_USERNAME,
                password=settings.SALESFORCE_PASSWORD,
                security_token=settings.SALESFORCE_TOKEN)

        stage = 'Proposal/Price Quote'
        now = datetime.date.today()
        close_date = now + datetime.timedelta(days=30)

        name = request.data['name']
        account = request.data['account_id']

        project = Order.objects.get(pk=request.data['project_id']) 
        pl = Price.objects.all()
        prices = {item.code:{'id': item.identifier, 'price': item.price} for item in Price.objects.all()}

        pricebook_name = request.data['services'][0]['pricebook']
        pricebook = PriceBook.objects.get(name=pricebook_name)

        crm_project_data = sf.Opportunity.create({
            'Name': name,
            'AccountId': account,
            'StageName': stage,
            'CloseDate': close_date.isoformat(),
            'VAT_Exempt__c': request.data['vat_exempt'],
            'Pricebook2Id': pricebook.identifier, 
            });

        crm_project = CRMProject(project_identifier=crm_project_data['id'], order=project)
        crm_project.save()

        quote_created = sf.Quote.create({
            'OpportunityId': crm_project_data['id'],
            'Name': name + ' quote',
            'Pricebook2Id': pricebook.identifier, 
            })

        request.data['services'].sort(key=lambda s: s['sample'])

        for item in request.data['services']:
            item_id = prices[item['code']]['id']

            quote_item = sf.QuoteLineItem.create({
                'QuoteId': quote_created['id'],
                'PricebookEntryId': item_id,
                'Description': item['sample'],
                'Quantity': item['quantity'],
                'UnitPrice': prices[item['code']]['price']
                })

        quote_data = sf.Quote.get(quote_created['id'])

        crm_quote = CRMQuote(project=crm_project, 
                quote_identifier=quote_data['Id'],
                quote_number=quote_data['QuoteNumber'],
                quote_name=quote_data['Name'],
                subtotal=quote_data['Subtotal'],
                discount=quote_data['Discount'],
                total=quote_data['TotalPrice'])
        crm_quote.save()

        return Response({'message': 'Project and quote created'})
