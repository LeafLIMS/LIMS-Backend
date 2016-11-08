
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

    @list_route()
    def updateall(self, request):
        get_pricebooks()
        return Response({'message': 'Pricebooks updated'})
