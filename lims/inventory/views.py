from io import TextIOWrapper

from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.conf import settings

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import DjangoModelPermissions, IsAdminUser
from rest_framework import filters

from lims.shared.pagination import PageNumberPaginationSmall, PageNumberOnlyPagination

from .models import (Set, GenericItem, Part, Enzyme, Primer, 
    PartType, ItemType, Consumable, Location, AmountMeasure)
from .serializers import * 
from .helpers import csv_to_items 

class LeveledMixin:
    def _to_leveled(self, obj):
        level = getattr(obj, obj._mptt_meta.level_attr) 
        if level == 0:
            display_value = obj.name 
        else:
            display_value = '{} {}'.format('--' * level, obj.name)
        return {
            'display_value': display_value, 
            'value': obj.name,
            'root': obj.get_root().name
        }


class MeasureViewSet(viewsets.ModelViewSet):
    queryset = AmountMeasure.objects.all()
    serializer_class = AmountMeasureSerializer
    permission_classes = (IsAdminUser, ) 
    search_fields = ('symbol', 'name',)

class ItemTypeViewSet(viewsets.ModelViewSet, LeveledMixin):
    queryset = ItemType.objects.all()
    serializer_class = ItemTypeSerializer
    permission_classes = (IsAdminUser, ) 
    search_fields = ('name',)

class LocationViewSet(viewsets.ModelViewSet, LeveledMixin):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (IsAdminUser, ) 
    search_fields = ('name',)

class InventoryViewSet(viewsets.ModelViewSet, LeveledMixin):
    queryset = GenericItem.objects.all().select_subclasses()
    serializer_class = GenericItemSerializer 
    permission_classes = (IsAdminUser, ) 
    filter_fields = ('in_inventory', 'item_type__name', 'identifier', 'name')
    search_fields = ('name', 'identifier', 'item_type__name', 'location__name',)

    def get_serializer_class_from_name(self, name):
        serializer_name = name + 'Serializer'
        serializer_class = globals()[serializer_name]
        return serializer_class

    def get_serializer_class(self):
        if self.request.method == 'POST' and hasattr(self.request, 'data') and 'of_type' in self.request.data:
            return self.get_serializer_class_from_name(
                    self.request.data['of_type'])
        else:
            try:
                obj = self.get_object()
                return self.get_serializer_class_from_name(obj.of_type())
            except:
                return self.serializer_class

    @list_route(methods=['POST'])
    def importitems(self, request):
        uploaded_file = request.data.get('items_file', None)
        response_data = {}
        if uploaded_file:
            f = TextIOWrapper(uploaded_file.file, enclimsg=request.enclimsg)
            saved, rejected = csv_to_items(f, request)
            response_data = {
                'saved': saved,
                'rejected': rejected
                }
        return Response(response_data)

class SetViewSet(viewsets.ModelViewSet):
    queryset = Set.objects.all()
    serializer_class = SetSerializer

    @detail_route()
    def items(self, request, pk=None):
        limit_to = request.query_params.get('limit_to', None)
        item = self.get_object()
        if limit_to:
            queryset = [o for o in item.items.all() if o.item_type.name == limit_to] 
        else:
            queryset = item.items.all()
        serializer = GenericItemSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def add(self, request, pk=None):
        item_id = request.query_params.get('id', None)
        inventoryset = self.get_object()
        if item_id:
            item = GenericItem.objects.get(pk=item_id)
            item.sets.add(inventoryset)
            return Response(status=201)
        return Response({message: 'The id of the item to add to the inventory is required'}, status=400)

    @detail_route(methods=['DELETE'])
    def remove(self, request, pk=None):
        item_id = request.query_params.get('id', None)
        inventoryset = self.get_object()
        if item_id:
            item = GenericItem.objects.get(pk=item_id)
            inventoryset.items.remove(item)
            return Response(status=201)
        return Response({message: 'The id of the item to add to the inventory is required'}, status=400)
