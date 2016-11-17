import datetime

from django.conf import settings
from django.contrib.auth.models import User

from simple_salesforce import Salesforce
from django_countries import countries

from lims.pricebook.models import Price, PriceBook
from .models import CRMAccount, CRMProject, CRMQuote


def CRMCreateContact(request, serialized_data):
    """
    Creates an accountless contact on the CRM system if they don't exist.
    """
    sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                    username=settings.SALESFORCE_USERNAME,
                    password=settings.SALESFORCE_PASSWORD,
                    security_token=settings.SALESFORCE_TOKEN)

    contact_id = ''
    account_id = ''

    contacts_query = ("SELECT Id,AccountId,FirstName,LastName,Email "
                      "FROM Contact WHERE Email = '{}'").format(serialized_data['email'])
    contacts = sf.query(contacts_query)
    if contacts['totalSize'] > 0:
        contact_id = contacts['records'][0]['Id']
        account_id = contacts['records'][0]['AccountId']
    else:
        country_codes = dict((value, key) for key, value in dict(countries).items())
        contact = sf.Contact.create({
            'FirstName': serialized_data['first_name'],
            'LastName': serialized_data['last_name'],
            'AccountId': account_id,
            'Email': serialized_data['email'],
            'MailingStreet':
                serialized_data['address_1'] + '\n ' + serialized_data.get('address_2', ''),
            'MailingCity': serialized_data['city'],
            'MailingPostalCode': serialized_data['postcode'],
            'MailingCountryCode': country_codes[serialized_data['country']],
        })
        contact_id = contact['id']

    if contact_id:
        user = User.objects.get(email=serialized_data['email'])

        details = CRMAccount(contact_identifier=contact_id,
                             user=user)
        if account_id:
            details.account_identifier = account_id
        details.save()

        return details
    return False


def CRMCreateProjectFromOrder(request, serialized_data):
    """
    Create a CRM Project and quote from a supplied order

    Used in views where a CRM project needs to be created (e.g. OrderView).
    """
    sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                    username=settings.SALESFORCE_USERNAME,
                    password=settings.SALESFORCE_PASSWORD,
                    security_token=settings.SALESFORCE_TOKEN)

    stage = 'Proposal/Price Quote'
    now = datetime.date.today()
    close_date = now + datetime.timedelta(days=30)

    # Get Pricebook data
    prices = {item.code: {'id': item.identifier, 'price': item.price}
              for item in Price.objects.all()}
    pricebook_name = serialized_data['data']['pricebook']
    try:
        pricebook = PriceBook.objects.get(name=pricebook_name)
    except:
        return False

    # Get User/CRMAccount data
    user = request.user
    try:
        account_id = user.crmaccount.account_identifier
    except:
        return False

    name = serialized_data['name']

    crm_project_data = sf.Opportunity.create({
        'Name': name,
        'AccountId': account_id,
        'StageName': stage,
        'CloseDate': close_date.isoformat(),
        'VAT_Exempt__c': serialized_data['data'].get('vat_exempt', False),
        'Pricebook2Id': pricebook.identifier,
    })

    crm_project = CRMProject(project_identifier=crm_project_data['id'],
                             name=name,
                             account=user.crmaccount)
    crm_project.save()

    quote_created = sf.Quote.create({
        'OpportunityId': crm_project_data['id'],
        'Name': name + ' quote',
        'Pricebook2Id': pricebook.identifier,
    })

    # Convert an obj to single list
    item_list = []
    for key, items in serialized_data['data'].items():
        if isinstance(items, list):
            item_list.extend(items)

    for item in item_list:
        item_id = prices[item['code']]['id']

        sf.QuoteLineItem.create({
            'QuoteId': quote_created['id'],
            'PricebookEntryId': item_id,
            'Description': item['label'],
            'Quantity': item['amount'],
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

    return crm_project
