import io
import ast

from django.core.exceptions import ObjectDoesNotExist

from pint import UnitRegistry, UndefinedUnitError

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import (OrderingFilter,
                                    SearchFilter,
                                    DjangoFilterBackend)

from lims.permissions.permissions import (IsInAdminGroupOrRO,
                                          ViewPermissionsMixin, ExtendedObjectPermissions,
                                          ExtendedObjectPermissionsFilter)
from lims.filetemplate.models import FileTemplate
from .models import Set, Item, ItemTransfer, ItemType, Location, AmountMeasure
from .serializers import (AmountMeasureSerializer, ItemTypeSerializer, LocationSerializer,
                          ItemSerializer, DetailedItemSerializer, SetSerializer)


class LeveledMixin:
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


class MeasureViewSet(viewsets.ModelViewSet):
    queryset = AmountMeasure.objects.all()
    serializer_class = AmountMeasureSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    search_fields = ('symbol', 'name',)


class ItemTypeViewSet(viewsets.ModelViewSet, LeveledMixin):
    queryset = ItemType.objects.all()
    serializer_class = ItemTypeSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    search_fields = ('name',)

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
    search_fields = ('name',)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.has_children():
            return Response({'message': 'Cannot delete Location with children'},
                            status=400)
        self.perform_destroy(instance)
        return Response(status=204)


class InventoryViewSet(viewsets.ModelViewSet, LeveledMixin, ViewPermissionsMixin):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)
    filter_fields = ('in_inventory', 'item_type__name', 'identifier', 'name')
    search_fields = ('name', 'identifier', 'item_type__name', 'location__name',)

    def get_serializer_class(self):
        if self.action == 'list':
            return self.serializer_class
        return DetailedItemSerializer

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(added_by=self.request.user)
        self.assign_permissions(instance, permissions)

    @list_route(methods=['POST'])
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
            # encoding = 'utf-8' if request.encoding is None else request.encoding
            # f = io.TextIOWrapper(uploaded_file.file, encoding=encoding)
            f = io.StringIO("".join(uploaded_file))
            items_to_import = filetemplate.read(f)
            saved = []
            rejected = []
            if items_to_import:
                for identifier, item_data in items_to_import.items():
                    item_data['identifier'] = ' '.join(identifier)
                    # item_data['assign_groups'] = json.loads(permissions)
                    item_data['assign_groups'] = permissions
                    if 'properties' not in item_data:
                        item_data['properties'] = []
                    else:
                        item_data['properties'] = ast.literal_eval(item_data['properties'])
                    item = DetailedItemSerializer(data=item_data)
                    if item.is_valid():
                        saved.append(item_data)
                        item, parsed_permissions = self.clean_serializer_of_permissions(item)
                        item.validated_data['added_by'] = request.user
                        instance = item.save()
                        self.assign_permissions(instance, parsed_permissions)
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
            ureg = UnitRegistry()

            raw_amount = transfer_details.get('amount', 0)
            raw_measure = transfer_details.get('measure', item.amount_measure.symbol)

            addition = transfer_details.get('is_addition', False)

            # Both measures must be valid in order to perform transfer.
            try:
                available = item.amount_available * ureg(item.amount_measure.symbol)
            except UndefinedUnitError:
                return Response(
                    {'message': 'Invalid item measure: %s' % item.amount_measure.symbol},
                    status=400)
            try:
                required = raw_amount * ureg(raw_measure)
            except UndefinedUnitError:
                return Response({'message': 'Invalid transfer measure: %s' % raw_measure},
                                status=400)

            is_complete = False
            is_addition = False

            if addition:
                new_amount = available + required
                is_complete = True
                is_addition = True
            else:
                if available < required:
                    missing = ((available - required) * -1)
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
            return Response({'message': 'Transfer {} created'.format(tfr.id)})
        return Response({'message': 'You must provide a transfer ID'}, status=400)


class SetViewSet(viewsets.ModelViewSet, ViewPermissionsMixin):
    queryset = Set.objects.all()
    serializer_class = SetSerializer
    permission_classes = (ExtendedObjectPermissions,)
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
            items = Item.objects.filter(pk=item_id)
            if items.count() > 0:
                item = Item.objects.get(pk=item_id)
                item.sets.add(inventoryset)
                return Response(status=201)
            return Response(
                {'message': 'The id of the item to add to the inventory is invalid'}, status=400)
        return Response(
            {'message': 'The id of the item to add to the inventory is required'}, status=400)

    @detail_route(methods=['DELETE'])
    def remove(self, request, pk=None):
        item_id = request.query_params.get('id', None)
        inventoryset = self.get_object()
        if item_id:
            items = Item.objects.filter(pk=item_id)
            if items.count() > 0:
                item = items.all()[0]
                inventoryset.items.remove(item)
                return Response(status=204)
            return Response(
                {'message': 'The id of the item to add to the inventory is invalid'}, status=400)
        return Response(
            {'message': 'The id of the item to add to the inventory is required'}, status=400)
