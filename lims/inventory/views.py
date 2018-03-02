import io
import json

from django.core.exceptions import ObjectDoesNotExist

from pint import UnitRegistry

import django_filters

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework import serializers
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.filters import (OrderingFilter,
                                    SearchFilter,
                                    DjangoFilterBackend)

from lims.permissions.permissions import (IsInAdminGroupOrRO,
                                          ViewPermissionsMixin, ExtendedObjectPermissions,
                                          ExtendedObjectPermissionsFilter)
from lims.shared.mixins import StatsViewMixin, AuditTrailViewMixin
from lims.filetemplate.models import FileTemplate
from lims.projects.models import Product
from .models import Set, Item, ItemTransfer, ItemType, Location, AmountMeasure
from .serializers import (AmountMeasureSerializer, ItemTypeSerializer, LocationSerializer,
                          ItemSerializer, DetailedItemSerializer, SetSerializer,
                          ItemTransferSerializer)
from .providers import InventoryItemPluginProvider


# Define as module level due to issues with file locking
# when calling a function requiring it multiple times
ureg = UnitRegistry()


class LeveledMixin(AuditTrailViewMixin):
    """
    Provide a display value for a heirarchy of elements
    """

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


class MeasureViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = AmountMeasure.objects.all()
    serializer_class = AmountMeasureSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    search_fields = ('symbol', 'name',)


class ItemTypeViewSet(viewsets.ModelViewSet, LeveledMixin):
    queryset = ItemType.objects.all()
    serializer_class = ItemTypeSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    search_fields = ('name', 'parent__name',)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.has_children():
            return Response({'message': 'Cannot delete ItemType with children'},
                            status=400)
        self.perform_destroy(instance)
        return Response(status=204)


class LocationViewSet(viewsets.ModelViewSet, LeveledMixin):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    search_fields = ('name', 'parent__name')

    def filter_queryset(self, queryset):
        queryset = super(LocationViewSet, self).filter_queryset(queryset)
        # Set ordering explicitly as django-filter borks the defaults
        return queryset.order_by('tree_id', 'lft')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.has_children():
            return Response({'message': 'Cannot delete Location with children'},
                            status=400)
        self.perform_destroy(instance)
        return Response(status=204)


class InventoryFilterSet(django_filters.FilterSet):
    """
    Filter for inventory items
    """
    class Meta:
        model = Item
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'added_by__username': ['exact'],
            'identifier': ['exact'],
            'barcode': ['exact'],
            'description': ['icontains'],
            'item_type__name': ['exact'],
            'location__name': ['exact'],
            'in_inventory': ['exact'],
            'amount_measure__symbol': ['exact'],
            'amount_available': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'concentration_measure__symbol': ['exact'],
            'concentration': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'added_on': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'last_updated_on': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'properties__name': ['exact', 'icontains'],
            'properties__value': ['exact', 'icontains'],
        }


class InventoryViewSet(LeveledMixin, StatsViewMixin, ViewPermissionsMixin, viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)
    search_fields = ('name', 'identifier', 'item_type__name', 'location__name',
                     'location__parent__name')
    filter_class = InventoryFilterSet

    def get_serializer_class(self):
        if self.action == 'list':
            return self.serializer_class
        return DetailedItemSerializer

    def get_object(self):
        instance = super().get_object()
        plugins = [p(instance) for p in InventoryItemPluginProvider.plugins]
        for p in plugins:
            p.view()
        return instance

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(added_by=self.request.user)
        self.assign_permissions(instance, permissions)
        plugins = [p(instance) for p in InventoryItemPluginProvider.plugins]
        for p in plugins:
            p.create()

    def perform_update(self, serializer):
        instance = serializer.save()
        plugins = [p(instance) for p in InventoryItemPluginProvider.plugins]
        for p in plugins:
            p.update()

    @list_route(methods=['POST'], parser_classes=(FormParser, MultiPartParser,))
    def importitems(self, request):
        """
        Import items from a CSV file

        Expects:
        file_template: The ID of the file template to use to parse the file
        items_file: The CSV file to parse
        permissions: Standard permissions format ({"name": "rw"}) to give to all items
        """
        file_template_id = request.data.get('filetemplate', None)
        uploaded_file = request.data.get('items_file', None)
        permissions = request.data.get('permissions', '{}')
        response_data = {}
        if uploaded_file and file_template_id:
            try:
                filetemplate = FileTemplate.objects.get(id=file_template_id)
            except FileTemplate.DoesNotExist:
                return Response({'message': 'File template does not exist'}, status=404)
            encoding = 'utf-8' if request.encoding is None else request.encoding
            f = io.TextIOWrapper(uploaded_file.file, encoding=encoding)
            items_to_import = filetemplate.read(f, as_list=True)
            saved = []
            rejected = []
            if items_to_import:
                for item_data in items_to_import:
                    item_data['assign_groups'] = json.loads(permissions)
                    if 'properties' not in item_data:
                        item_data['properties'] = []
                    '''
                    I'm not actually sure what this was supposed to do!
                    Properties are already list so this shouldn't be required.
                    else:
                        item_data['properties'] = ast.literal_eval(item_data['properties'])
                    '''
                    item = DetailedItemSerializer(data=item_data)
                    if item.is_valid():
                        saved.append(item_data)
                        item, parsed_permissions = self.clean_serializer_of_permissions(item)
                        item.validated_data['added_by'] = request.user
                        instance = item.save()
                        self.assign_permissions(instance, parsed_permissions)
                        if 'product' in item_data:
                            try:
                                prod = item_data['product']
                                product = Product.objects.get(product_identifier=prod)
                            except:
                                pass
                            else:
                                product.linked_inventory.add(instance)
                    else:
                        item_data['errors'] = item.errors
                        rejected.append(item_data)
            else:
                return Response({'message': 'File is format is incorrect'}, status=400)
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

            raw_amount = float(transfer_details.get('amount', 0))
            raw_measure = transfer_details.get('measure', item.amount_measure.symbol)

            addition = transfer_details.get('is_addition', False)

            # Booleanise them
            is_complete = False
            is_addition = False
            if addition:
                is_addition = True
                is_complete = True

            if transfer_details.get('transfer_complete', False):
                is_complete = True

            try:
                measure = AmountMeasure.objects.get(symbol=raw_measure)
            except AmountMeasure.DoesNotExist:
                raise serializers.ValidationError({'message':
                                                   'Measure {} does not exist'.format(raw_measure)
                                                   })

            tfr = ItemTransfer(
                item=item,
                amount_taken=raw_amount,
                amount_measure=measure,
                barcode=transfer_details.get('barcode', ''),
                coordinates=transfer_details.get('coordinates', ''),
                transfer_complete=is_complete,
                is_addition=is_addition
            )

            transfer_status = tfr.check_transfer()
            if transfer_status[0] is True:
                tfr.save()
                tfr.do_transfer(ureg)
            else:
                return Response(
                    {'message': 'Inventory item {} ({}) is short of amount by {}'.format(
                     item.identifier, item.name, transfer_status[1])}, status=400)
            return Response({'message': 'Transfer {} created'.format(tfr.id)})
        return Response({'message': 'You must provide a transfer ID'}, status=400)

    @detail_route(methods=['POST'])
    def cancel_transfer(self, request, pk=None):
        """
        Cancel an active transfer, adding the amount back
        """
        tfr_id = request.query_params.get('id', None)

        if tfr_id:
            try:
                tfr = ItemTransfer.objects.get(pk=tfr_id, transfer_complete=False)
            except ObjectDoesNotExist:
                return Response({'message': 'No item transfer exists with that ID'}, status=404)
            tfr.is_addition = True
            tfr.do_transfer(ureg)
            tfr.delete()
            return Response({'message': 'Transfer cancelled'})
        return Response({'message': 'You must provide a transfer ID'}, status=400)


class SetViewSet(AuditTrailViewMixin, viewsets.ModelViewSet, ViewPermissionsMixin):
    queryset = Set.objects.all()
    serializer_class = SetSerializer
    permission_classes = (ExtendedObjectPermissions,)
    search_fields = ('name',)
    filter_fields = ('is_partset',)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save()
        self.assign_permissions(instance, permissions)

    @detail_route()
    def items(self, request, pk=None):
        limit_to = request.query_params.get('limit_to', None)
        item = self.get_object()
        if limit_to:
            queryset = [o for o in item.items.all() if o.item_type.name == limit_to]
        else:
            queryset = item.items.all()
        serializer = ItemSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def add(self, request, pk=None):
        item_id = request.query_params.get('id', None)
        inventoryset = self.get_object()
        if item_id:
            try:
                item = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                raise serializers.ValidationError({'message':
                                                   'Item {} does not exist'.format(item_id)})
            item.sets.add(inventoryset)
            return Response(status=201)
        return Response(
            {'message': 'The id of the item to add to the inventory is required'}, status=400)

    @detail_route(methods=['DELETE'])
    def remove(self, request, pk=None):
        item_id = request.query_params.get('id', None)
        inventoryset = self.get_object()
        if item_id:
            try:
                item = inventoryset.items.get(pk=item_id)
            except Item.DoesNotExist:
                raise serializers.ValidationError({'message':
                                                   'Item {} does not exist'.format(item_id)})
            inventoryset.items.remove(item)
            return Response(status=204)
        return Response(
            {'message': 'The id of the item to add to the inventory is required'}, status=400)


class ItemTransferViewSet(AuditTrailViewMixin, viewsets.ReadOnlyModelViewSet, ViewPermissionsMixin):
    queryset = ItemTransfer.objects.all()
    serializer_class = ItemTransferSerializer
    search_fields = ('item__name', 'item__identifier', 'barcode',)
    filter_fields = ('transfer_complete', 'barcode',)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter,)

    def get_queryset(self):
        return ItemTransfer.objects.filter(transfer_complete=False)

    @list_route(methods=['GET'])
    def grouped(self, request):
        """
        Group transfers under the same barcode e.g. as if they where in plates.

        Limit allows to set how many barcodes are fetched.
        """
        limit = int(request.query_params.get('limit', 10))
        qs = (ItemTransfer.objects.filter(transfer_complete=False)
                                  .distinct('barcode')
                                  .order_by('barcode', '-date_created')[:limit])
        barcodes = [i.barcode for i in qs]
        transfers = (ItemTransfer.objects.filter(transfer_complete=False, barcode__in=barcodes)
                                         .order_by('barcode', 'coordinates'))
        serializer = ItemTransferSerializer(transfers, many=True)
        groups = {}
        for t in serializer.data:
            if t['barcode'] not in groups:
                groups[t['barcode']] = []
            groups[t['barcode']].append(t)
        return Response(groups)
