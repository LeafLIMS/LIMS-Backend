from io import TextIOWrapper
import json
import copy
import uuid

from pint import UnitRegistry, UndefinedUnitError
from django.core.exceptions import ObjectDoesNotExist

from django.utils import timezone
from guardian.shortcuts import get_group_perms

import django_filters

from rest_framework import viewsets
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.validators import ValidationError
from rest_framework.filters import (OrderingFilter,
                                    SearchFilter,
                                    DjangoFilterBackend)
from rest_framework.reverse import reverse
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework_csv.renderers import CSVRenderer

from lims.shared.filters import ListFilter
from lims.permissions.permissions import (ViewPermissionsMixin,
                                          ExtendedObjectPermissions,
                                          ExtendedObjectPermissionsFilter)

from lims.shared.mixins import StatsViewMixin, AuditTrailViewMixin
from lims.filetemplate.models import FileTemplate
from lims.inventory.models import (Item, ItemTransfer, AmountMeasure, Location,
                                   ItemType)
from lims.inventory.serializers import ItemTransferPreviewSerializer
# Disable flake8 on this line as we need the templates to be imported but
# they do not appear to be used (selected from globals)
from .models import (Workflow,  # noqa
                     Run, RunLabware,  # noqa
                     TaskTemplate, InputFieldTemplate, OutputFieldTemplate,  # noqa
                     StepFieldTemplate, VariableFieldTemplate,  # noqa
                     CalculationFieldTemplate)  # noqa
from .serializers import (WorkflowSerializer, SimpleTaskTemplateSerializer,  # noqa
                          TaskTemplateSerializer,  # noqa
                          TaskValuesSerializer,  # noqa
                          RunSerializer,  # noqa
                          DetailedRunSerializer,  # noqa
                          InputFieldTemplateSerializer,  # noqa
                          OutputFieldTemplateSerializer,  # noqa
                          VariableFieldTemplateSerializer,  # noqa
                          VariableFieldValueSerializer,  # noqa
                          StepFieldTemplateSerializer,  # noqa
                          CalculationFieldTemplateSerializer,  # noqa
                          RecalculateTaskTemplateSerializer)  # noqa
from lims.datastore.models import DataEntry
from lims.datastore.serializers import DataEntrySerializer
from lims.equipment.models import Equipment


class WorkflowViewSet(AuditTrailViewMixin, ViewPermissionsMixin, viewsets.ModelViewSet):
    """
    Provide a list of workflow templates that are available.

    ### query_params

    - _search_: search workflow name and created_by
    """
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    search_fields = ('name', 'created_by__username',)
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(created_by=self.request.user)
        self.assign_permissions(instance, permissions)

    @detail_route()
    def tasks(self, request, pk=None):
        workflow = self.get_object()
        serializer = self.get_serializer(workflow)
        result = serializer.data
        tasklist = []
        tasks = self.get_object().get_tasks()
        for t in tasks:
            serializer_task = SimpleTaskTemplateSerializer(t)
            tasklist.append(serializer_task.data)
        result['tasks'] = tasklist
        return Response(result)

    @detail_route()
    def task_details(self, request, pk=None):
        """
        Get a detailed version of a specific task.

        ### query_params

        - _position_ (**required**): The task position in the workflow
        """
        workflow = self.get_object()
        position = request.query_params.get('position', None)
        if position:
            try:
                taskId = workflow.order.split(',')[int(position)]
                task = TaskTemplate.objects.get(pk=taskId)
                serializer = TaskTemplateSerializer(task)
                result = serializer.data
            except IndexError:
                return Response({'message': 'Invalid position'}, status=400)
            except ObjectDoesNotExist:
                return Response({'message': 'Task does not exist'}, status=400)
            return Response(result)
        return Response({'message': 'Please provide a task position'}, status=400)


class RunViewSet(AuditTrailViewMixin, ViewPermissionsMixin, StatsViewMixin, viewsets.ModelViewSet):
    """
    List all runs, active only be default
    """
    queryset = Run.objects.all()
    serializer_class = RunSerializer
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)
    filter_fields = ('is_active', 'task_in_progress', 'has_started',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_serializer_class(self):
        """
        Provide a more detailed serializer when not a list
        """
        if self.action == 'retrieve':
            return DetailedRunSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        # TODO:
        # Check tasks permissions valid
        # Check product permissions valid
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(started_by=self.request.user)
        self.assign_permissions(instance, permissions)

    def _get_product_input_items(self, input_type):
        """
        Get input items from products in the run
        """
        run = self.get_object()
        task_input_items = {}
        for p in run.products.all():
            task_input_items[p] = list(p.linked_inventory.filter(item_type__name=input_type))
        return task_input_items

    def _generate_data_dict(self, input_items, task_data):
        """
        Generate data items from supplied task data

        One data item to each product to be produced.
        """
        # Link (product,item) -> serialized_data
        data_items = {}
        for product, items in input_items.items():
            key = product.product_identifier
            data_items[key] = copy.deepcopy(task_data.validated_data)
            # Now add the input items to the dict
            # Get data from task to put basic together
            data_items[key]['product_inputs'] = {}
            for itm in items:
                itm_data = {
                    'amount': task_data.validated_data['product_input_amount'],
                    'measure': task_data.validated_data['product_input_measure'],
                }
                data_items[key]['product_inputs'][itm.identifier] = itm_data
        return data_items

    def _update_data_items_from_file(self, file_data, data_items):
        """
        Process input file data in update data dict with new values
        """
        # TODO: Process file to allow product/item updates easily
        for f in file_data:
            try:
                ft = FileTemplate.objects.get(name=f.name)
            except:
                pass
            else:
                parsed_file = ft.read(TextIOWrapper(f.file, encoding=f.charset))
                if parsed_file:
                    for key, row in parsed_file.items():
                        data_items[key].update(row)
                else:
                    message = {
                        'message':
                            'Input file "{}" has incorrect headers/format'.format(f.name)}
                    raise ValidationError(message)
        return data_items

    def _as_measured_value(self, amount, measure):
        """
        Convert if possible to a value with units
        """
        if type(amount) is not float:
            amount = float(amount)
        try:
            value = amount * self.ureg(measure)
        except UndefinedUnitError:
            value = amount * self.ureg.count
        return value

    def _get_from_inventory(self, identifier):
        """
        Get an item from the inventory based on identifier
        """
        try:
            item = Item.objects.get(identifier=identifier)
        except Item.DoesNotExist:
            message = {'message': 'Item {} does not exist !'.format(identifier)}
            raise serializers.ValidationError(message)
        return item

    def _update_amounts(self, item, amount, store, field):
        """
        Referenced update of an amount indexed by identifier
        """
        if item not in store:
            store[item] = {'amount': amount,
                           'barcode': field.get('destintion_barcode', None),
                           'coordinates': field.get('destination_coordinates', None)}
        else:
            store[item]['amount'] += amount

    def _update_item_amounts(self, field, key, data_item_amounts, sum_item_amounts):
        """
        Referenced update of item amounts + sum item amounts
        """
        amount = self._as_measured_value(field['amount'], field['measure'])
        item = self._get_from_inventory(field['inventory_identifier'])
        data_item_amounts[key][item] = amount
        self._update_amounts(item, amount, sum_item_amounts, field)

    def _get_item_amounts(self, data_items, task_data):
        """
        Get the per-product and total sum of items needed for task
        """
        sum_item_amounts = {}
        data_item_amounts = {}

        # Get labware amounts
        labware_identifier = task_data.validated_data['labware_identifier']
        labware_item = self._get_from_inventory(labware_identifier)
        labware_required = task_data.validated_data['labware_amount']
        labware_barcode = task_data.validated_data.get('labware_barcode', None)
        labware_symbol = None
        if labware_item.amount_measure is not None:
            labware_symbol = labware_item.amount_measure.symbol
        sum_item_amounts[labware_item] = {
                'amount': self._as_measured_value(labware_required, labware_symbol),
                'barcode': labware_barcode,
        }

        # Get task input field amounts
        for key, item in data_items.items():
            data_item_amounts[key] = {}
            for field in item['input_fields']:
                self._update_item_amounts(field, key, data_item_amounts, sum_item_amounts)

            for identifier, field in item['product_inputs'].items():
                field['inventory_identifier'] = identifier
                self._update_item_amounts(field, key, data_item_amounts, sum_item_amounts)
        return (data_item_amounts, sum_item_amounts)

    def _check_input_amounts(self, sum_item_amounts):
        """
        Check there is enough for each item available
        """
        errors = []
        valid_amounts = True
        for item, required in sum_item_amounts.items():
            available = self._as_measured_value(item.amount_available, item.amount_measure.symbol)
            if available < required['amount']:
                missing = (available - required['amount']) * -1
                message = 'Inventory item {0} ({1}) is short of amount by {2:.2f}'.format(
                    item.identifier, item.name, missing)
                errors.append(message)
                valid_amounts = False
        return (valid_amounts, errors)

    def _create_item_transfers(self, sum_item_amounts):
        """
        Create ItemTransfers to alter inventory amounts
        """
        transfers = []
        for item, amount in sum_item_amounts.items():
            try:
                amount_symbol = '{:~}'.format(amount['amount']).split(' ')[1]
                measure = AmountMeasure.objects.get(symbol=amount_symbol)
                amount['amount'] = amount['amount'].magnitude
            except:
                measure = AmountMeasure.objects.get(symbol='items')
            transfers.append(ItemTransfer(
                item=item,
                barcode=amount.get('barcode', None),
                coordinates=amount.get('coordinates', None),
                amount_taken=amount['amount'],
                amount_measure=measure))
        return transfers

    def _serialize_item_amounts(self, dict_of_amounts):
        output = []
        for item, amount in dict_of_amounts.items():
            output.append({
                'name': item.name,
                'identifier': item.identifier,
                'amount': amount.magnitude,
                'measure': '{:~}'.format(amount).split(' ')[1],
            })
        return output

    def _do_driver_actions(self, task_data):
        pass

    @detail_route(methods=['POST'])
    # Do not accept JSON as cannot send files this way
    @parser_classes((FormParser, MultiPartParser,))
    def start_task(self, request, pk=None):
        """
        Check input values and start or preview a task

        Takes in task data, any files and calculates if the data
        is valid to run the task. Pass is_check to check but not
        run the task.
        """
        # Get task data from request as may have been edited to
        # suit current situation.
        task_data = json.loads(self.request.data.get('task', '{}'))
        serialized_task = TaskValuesSerializer(data=task_data)

        # Get a list of input file data to be parsed
        file_data = self.request.data.getlist('input_files', [])

        # Perform checks on the validity of the data before the
        # task is run, return inventory requirements.
        is_check = request.query_params.get('is_check', False)
        # Is this a repeat of a failed task
        # is_repeat = request.query_params.get('is_repeat', False)

        if serialized_task.is_valid(raise_exception=True):
            # Init a unit registry for later use
            self.ureg = UnitRegistry()

            run = self.get_object()
            task = run.get_task_at_index(run.current_task)

            # Get items from products
            product_type = serialized_task.validated_data['product_input']
            product_input_items = self._get_product_input_items(product_type)

            # Process task data against input_items
            data_items = self._generate_data_dict(product_input_items,
                                                  serialized_task)
            # Process input files against task data
            data_items = self._update_data_items_from_file(file_data,
                                                           data_items)
            product_item_amounts, sum_item_amounts = self._get_item_amounts(data_items,
                                                                            serialized_task)
            valid_amounts, errors = self._check_input_amounts(sum_item_amounts)

            transfers = self._create_item_transfers(sum_item_amounts)

            # Check if you can actually use the equipment
            equipment_name = serialized_task.validated_data['equipment_choice']
            try:
                equipment = Equipment.objects.get(name=equipment_name)
            except Equipment.DoesNotExist:
                raise serializers.ValidationError({'message':
                                                  'Equipment does not exist!'})

            if is_check:
                check_output = {
                    'equipment_status': equipment.status,
                    'errors': errors,
                    'requirements': []
                }
                for t in transfers:
                    st = ItemTransferPreviewSerializer(t)
                    check_output['requirements'].append(st.data)
                return Response(check_output)
            else:
                if equipment.status != 'idle':
                    raise serializers.ValidationError({'message':
                                                      'Equipment is currently in use'})

                if not valid_amounts:
                    raise ValidationError({'message': '\n'.join(errors)})
                task_run_identifier = uuid.uuid4()
                # driver_output = self._do_driver_actions(data_items)
                # Generate DataItem for inputs
                for product in run.products.all():
                    prod_amounts = product_item_amounts[product.product_identifier]
                    data_items[product.product_identifier]['product_input_amounts'] = \
                        self._serialize_item_amounts(prod_amounts)
                    entry = DataEntry(
                        run=run,
                        task_run_identifier=task_run_identifier,
                        product=product,
                        created_by=self.request.user,
                        state='active',
                        data=data_items[product.product_identifier],
                        task=task)
                    entry.save()

                # TODO: RunLabware creation
                # Link labeware barcode -> transfer
                # At this point transfers have the amount taken but are not complete
                # until task finished
                for t in transfers:
                    t.run_identifier = task_run_identifier
                    t.do_transfer(self.ureg)
                    t.save()
                    run.transfers.add(t)

                # Update run with new details
                run.task_in_progress = True
                run.has_started = True
                run.task_run_identifier = task_run_identifier
                run.save()
                return Response({'message': 'Task started successfully'})

    @detail_route(methods=["POST"])
    def cancel_task(self, request, pk=None):
        """
        Cancel a running task that has accidentally been started
        """
        run = self.get_object()

        if run.task_in_progress:
            ureg = UnitRegistry()
            # Get any transfers for this task
            transfers_for_this_task = run.transfers.filter(run_identifier=run.task_run_identifier)
            data_entries = DataEntry.objects.filter(task_run_identifier=run.task_run_identifier)
            # Transfer all the things taken back into the inventory
            for t in transfers_for_this_task:
                t.is_addition = True
                t.do_transfer(ureg)
            # Once transfers made delete them
            transfers_for_this_task.delete()
            # Trash the data entries now as they're irrelevant
            data_entries.delete()
            # No longer active
            run.task_in_progress = False
            run.has_started = False
            run.save()
            return Response({'message': 'Task cancelled'})
        return Response({'message': 'Task not in progress so cannot be cancelled'}, status=400)

    @detail_route(methods=["POST"])
    def recalculate(self, request, pk=None):
        """
        Given task data recalculate and return task.
        """
        obj = self.get_object()
        task_data = request.data
        if task_data:
            serializer = RecalculateTaskTemplateSerializer(data=task_data)
            if serializer.is_valid(raise_exception=True):
                return Response(serializer.data)  # Raw data, not objects
        serializer = TaskTemplateSerializer(obj)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data)  # Raw data, not objects

    @detail_route()
    def monitor_task(self, request, pk=None):
        """
        Check up on a running task
        """
        run = self.get_object()

        if run.task_in_progress and run.is_active:
            task = run.get_task_at_index(run.current_task)
            transfers = run.transfers.filter(run_identifier=run.task_run_identifier)
            serialized_transfers = ItemTransferPreviewSerializer(transfers, many=True)
            # Get current data for each product
            data_entries = DataEntry.objects.filter(task_run_identifier=run.task_run_identifier)
            serialized_data_entries = DataEntrySerializer(data_entries, many=True)
            # Get driver files
            # It will a file template for now
            # But ultimetly a driver will step in and do some processing
            # Will need UI/task stuff for that
            equipment_files = []
            for ft in task.equipment_files.all():
                equipment_files.append({
                    'name': ft.name,
                    'id': ft.id,
                })
            output_data = {
                'transfers': serialized_transfers.data,
                'data': serialized_data_entries.data,
                'equipment_files': equipment_files,
            }
            # What stage is the task at? Talk to driver/equipment
            return Response(output_data)
        # Return a 204 as there is no task to monitor
        return Response(status=204)

    @detail_route(methods=['GET'], renderer_classes=(CSVRenderer,))
    def get_file(self, request, pk=None):
        file_id = request.query_params.get('id', None)

        run = self.get_object()
        task = run.get_task_at_index(run.current_task)

        try:
            file_template = task.equipment_files.get(id=file_id)
        except ObjectDoesNotExist:
            raise ValidationError({'message': 'Template does not exist'})

        if run.task_in_progress and run.is_active:
            transfers = run.transfers.filter(run_identifier=run.task_run_identifier)
            serialized_transfers = ItemTransferPreviewSerializer(transfers, many=True)
            data_entries = DataEntry.objects.filter(task_run_identifier=run.task_run_identifier)
            serialized_data_entries = DataEntrySerializer(data_entries, many=True)
            output_data = task.data_to_output_file(file_template,
                                                   serialized_data_entries.data,
                                                   serialized_transfers.data)
            return Response(output_data)
        # Return a 204 as there is no task to get files for
        return Response(status=204)

    def _copy_files(self, data_entries):
        task = self.get_object().get_task_at_index(self.get_object().current_task)
        # If no choice default to the first entry in the equipment
        # for use on
        equipment_choice = data_entries[0].data.get('equipment_choice', None)
        try:
            equipment = task.capable_equipment.get(name=equipment_choice)
        except:
            # Well we can't do anything so just return
            return
        for file_to_copy in equipment.files_to_copy.filter(is_enabled=True):
            interpolate_dict = {
                'run_identifier': str(data_entries[0].task_run_identifier),
            }
            for loc in file_to_copy.locations.all():
                file_store = loc.copy(interpolate_dict)
                if file_store:
                    for d in data_entries:
                        d.data_files.add(file_store)
                        d.save()

    @detail_route(methods=['POST'])
    def finish_task(self, request, pk=None):
        """
        Finish a running task, completing run if required
        """
        # If it is manually, rather than a system, finish to the task
        # is_manual_finish = request.query_params.get('manual', False)
        # A comma seperated list of product ID's that failed the task
        product_failures = request.data.get('failures', None)

        run = self.get_object()

        if run.task_in_progress and run.is_active:

            # Now the task is complete any transfers can be marked as complete
            transfers = run.transfers.filter(run_identifier=run.task_run_identifier)
            for t in transfers:
                t.transfer_complete = True
                t.save()

            failed_products = []
            if product_failures:
                # If failures create new run based on current
                # and move failed products to it
                failure_ids = str(product_failures).split(',')
                failed_products = run.products.filter(id__in=failure_ids)
                new_name = '{} (failed)'.format(run.name)
                new_run = Run(
                    name=new_name,
                    tasks=run.tasks,
                    current_task=run.current_task,
                    has_started=True,
                    started_by=request.user)
                new_run.save()
                new_run.products.add(*failed_products)

                # Update data entries state to failed
                # This variable exists for line length purposes :P
                rtri = run.task_run_identifier
                failed_entries = DataEntry.objects.filter(task_run_identifier=rtri,
                                                          product__in=failed_products)
                failed_entries.update(state='failed')

                # Remove the failed products from the current run
                run.products.remove(*failed_products)

            # find and mark dataentry complete!
            entries = DataEntry.objects.filter(
                task_run_identifier=run.task_run_identifier,
                product__in=run.products.all()).exclude(product__in=failed_products)
            entries.update(state='succeeded')

            # mark labware inactive
            active_labware = run.labware.filter(is_active=True)
            active_labware.update(is_active=False)

            # Handle filepath copy stuff
            self._copy_files(entries)

            # Create ouputs from the task
            runindex = 0
            for e in entries:
                for index, output in enumerate(e.data['output_fields']):
                    output_name = '{} {}/{}'.format(e.product.product_identifier,
                                                    e.product.name,
                                                    output['label'])
                    measure = AmountMeasure.objects.get(symbol=output['measure'])
                    identifier = '{}/{}/{}'.format(run.task_run_identifier,
                                                   runindex, index)
                    runindex += 1
                    location = Location.objects.get(name='Lab')
                    item_type = ItemType.objects.get(name=output['lookup_type'])
                    new_item = Item(
                        name=output_name,
                        identifier=identifier,
                        item_type=item_type,
                        location=location,
                        amount_available=output['amount'],
                        amount_measure=measure,
                        added_by=request.user,
                    )
                    new_item.save()

                    product_input_ids = [p for p in e.data['product_inputs']]
                    product_items = Item.objects.filter(identifier__in=product_input_ids)
                    new_item.created_from.add(*product_items)

                    e.product.linked_inventory.add(new_item)
                    e.save()

            run.task_in_progress = False

            # advance task by one OR end if no more tasks
            if run.current_task == len(run.get_task_list()) - 1:
                run.is_active = False
                run.date_finished = timezone.now()
            else:
                run.current_task += 1

            run.save()
            serializer = RunSerializer(run)
            return Response(serializer.data)
        # Return a 204 as there is no task to monitor
        return Response(status=204)

    @detail_route(methods=['POST'])
    def workflow_from_run(self, request, pk=None):
        """
        Take a current run and create a workflow from tasks
        """
        new_name = request.query_params.get('name', None)
        if new_name:
            run = self.get_object()
            new_workflow = Workflow(
                name=new_name,
                order=run.tasks,
                created_by=request.user)
            new_workflow.save()
            location = reverse('workflows-detail', args=[new_workflow.id])
            return Response(headers={'location': location}, status=303)
        else:
            return Response({'message': 'Please supply a name'}, status=400)


class TaskFilterSet(django_filters.FilterSet):
    """
    Filter for the TaskViewSet
    """
    id__in = ListFilter(name='id')

    class Meta:
        model = TaskTemplate
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact'],
            'created_by__username': ['exact'],
        }


class TaskViewSet(AuditTrailViewMixin, ViewPermissionsMixin, viewsets.ModelViewSet):
    """
    Provide a list of TaskTemplates available
    """
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)
    search_fields = ('name', 'created_by__username',)
    filter_class = TaskFilterSet

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(created_by=self.request.user)
        self.assign_permissions(instance, permissions)

    @detail_route(methods=["POST"])
    def recalculate(self, request, pk=None):
        """
        Given task data recalculate and return task.
        """
        obj = self.get_object()
        task_data = request.data
        if task_data:
            serializer = RecalculateTaskTemplateSerializer(data=task_data)
            if serializer.is_valid(raise_exception=True):
                return Response(serializer.data)  # Raw data, not objects
        serializer = TaskTemplateSerializer(obj)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data)  # Raw data, not objects


class TaskFieldViewSet(AuditTrailViewMixin, ViewPermissionsMixin, viewsets.ModelViewSet):
    """
    Provides a list of all task fields
    """
    ordering_fields = ('name',)
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)

    def get_serializer_class(self):
        try:
            type_name = self.request.query_params.get('type', '').title()
            if type_name:
                serializer_name = type_name + 'FieldTemplateSerializer'
                serializer_class = globals()[serializer_name]
                return serializer_class
        except:
            pass
        return InputFieldTemplateSerializer

    def get_queryset(self):
        """
        Pick the type of field so it can be properly serialized.
        """
        type_name = self.request.query_params.get('type', '').title()
        if type_name:
            object_name = type_name + 'FieldTemplate'
            object_class = globals()[object_name]
            return object_class.objects.all()
        return InputFieldTemplate.objects.all()

    def perform_create(self, serializer):
        task_template = serializer.validated_data['template']
        if ('view_tasktemplate' in get_group_perms(self.request.user, task_template)
                or self.request.user.groups.filter(name='admin').exists()):
            if ('change_tasktemplate' in get_group_perms(self.request.user, task_template)
                    or self.request.user.groups.filter(name='admin').exists()):
                instance = serializer.save()
                self.clone_group_permissions(instance.template, instance)
            else:
                raise PermissionDenied('You do not have permission to create this')
        else:
            raise NotFound()
