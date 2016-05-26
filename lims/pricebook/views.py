from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from .models import PriceBook
from .serializers import PriceBookSerializer
from lims.pricebook.management.commands.getpricebooks import get_pricebooks

class PriceBookViewSet(viewsets.ModelViewSet):
    queryset = PriceBook.objects.all()
    serializer_class = PriceBookSerializer

    @list_route()
    def updateall(self, request):
        get_pricebooks()
        return Response({'message': 'Pricebooks updated'})

