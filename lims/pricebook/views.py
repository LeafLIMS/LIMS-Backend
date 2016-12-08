from django.conf import settings

from simple_salesforce import Salesforce

from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from lims.permissions.permissions import IsInAdminGroupOrRO
from lims.shared.mixins import AuditTrailViewMixin

from .models import PriceBook
from .serializers import PriceBookSerializer
from lims.pricebook.management.commands.getpricebooks import get_pricebooks


class PriceBookViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = PriceBook.objects.all()
    serializer_class = PriceBookSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    filter_fields = ('name', 'identifier',)

    def perform_create(self, serializer):
        serializer.save()
        get_pricebooks()

    @list_route(methods=['POST'])
    def updateall(self, request):
        get_pricebooks()
        return Response({'message': 'Pricebooks updated'})

    @list_route()
    def on_crm(self, request):
        """
        List of all pricebooks available on thr CRM
        """
        sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                        username=settings.SALESFORCE_USERNAME,
                        password=settings.SALESFORCE_PASSWORD,
                        security_token=settings.SALESFORCE_TOKEN)

        pricebooks = sf.query("SELECT id,name FROM Pricebook2")
        return Response(pricebooks['records'])
