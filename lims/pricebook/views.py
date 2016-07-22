
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from lims.permissions.permissions import IsInAdminGroupOrRO

from .models import PriceBook
from .serializers import PriceBookSerializer
from lims.pricebook.management.commands.getpricebooks import get_pricebooks


class PriceBookViewSet(viewsets.ModelViewSet):
    queryset = PriceBook.objects.all()
    serializer_class = PriceBookSerializer
    permission_classes = (IsInAdminGroupOrRO,)

    @list_route()
    def updateall(self, request):
        get_pricebooks()
        return Response({'message': 'Pricebooks updated'})
