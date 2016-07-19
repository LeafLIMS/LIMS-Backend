from io import TextIOWrapper

from django.core.exceptions import ObjectDoesNotExist

from pint import UnitRegistry, UndefinedUnitError

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAdminUser


from .models import (Set, Item, GenericItem, ItemTransfer,
                     ItemType, Location, AmountMeasure)
from .serializers import (AmountMeasureSerializer, ItemTypeSerializer,
                          LocationSerializer, ItemSerializer, DetailedItemSerializer,
                          SetSerializer, GenericItemSerializer)
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
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = (IsAdminUser, )
    filter_fields = ('in_inventory', 'item_type__name', 'identifier', 'name')
    search_fields = ('name', 'identifier', 'item_type__name', 'location__name',)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedItemSerializer
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

    @detail_route(methods=['POST'])
    def transfer(self, request, pk=None):
        """
        Either create or complete an item transfer.
        """
        tfr_id = request.query_params.get('id', None)
        complete_transfer = request.query_params.get('complete', False)

        transfer_details = request.data

        if tfr_id and complete_transfer:
            try:
                tfr = ItemTransfer.objects.get(pk=tfr_id)
            except ObjectDoesNotExist:
                return Response({'message': 'No item transfer exists with that ID'}, status=404)
            tfr.transfer_complete = True
            tfr.save()
            return Response({'message': 'Transfer {} complete'.format(tfr_id)})
        elif transfer_details:
            item = self.get_object()
            ureg = UnitRegistry()

            raw_amount = transfer_details.get('amount', 0)
            raw_measure = transfer_details.get('measure', item.amount_measure.symbol)

            addition = transfer_details.get('is_addition', False)

            try:
                available = item.amount_available * ureg(item.amount_measure.symbol)
            except UndefinedUnitError:
                available = item.amount_available

            try:
                required = raw_amount * ureg(raw_measure)
            except UndefinedUnitError:
                required = raw_amount

            is_complete = False
            is_addition = False

            if addition:
                new_amount = available + required
                is_complete = True
                is_addition = True
            else:
                if available < required:
                    missing = (available - required * -1)
                    return Response(
                        {'message': 'Inventory item {} ({}) is short of amount by {}'.format(
                         item.identifier, item.name, missing)}, status=400)
                new_amount = available - required

            item.amount_available = new_amount.magnitude
            item.save()

            tfr = ItemTransfer(
                item=item,
                amount_taken=required.magnitude,
                amount_measure=AmountMeasure.objects.get(symbol=raw_measure),
                barcode=transfer_details.get('barcode', ''),
                coordinates=transfer_details.get('coodinates', ''),
                transfer_complete=is_complete,
                is_addition=is_addition
            )
            tfr.save()
            return Response({'message': 'Transfer created'})
        return Response({'message': 'You must provide a transfer ID'}, status=400)


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
        return Response(
            {'message': 'The id of the item to add to the inventory is required'}, status=400)

    @detail_route(methods=['DELETE'])
    def remove(self, request, pk=None):
        item_id = request.query_params.get('id', None)
        inventoryset = self.get_object()
        if item_id:
            item = GenericItem.objects.get(pk=item_id)
            inventoryset.items.remove(item)
            return Response(status=201)
        return Response(
            {'message': 'The id of the item to add to the inventory is required'}, status=400)
