from operator import itemgetter
from uuid import uuid4
from io import TextIOWrapper
import json
from itertools import groupby
import datetime

from pint import UnitRegistry, UndefinedUnitError


from django.core.exceptions import ObjectDoesNotExist

import django_filters

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAdminUser, DjangoObjectPermissions


from lims.shared.filters import ListFilter

from lims.projects.models import Product
from lims.filetemplate.models import FileTemplate
from lims.inventory.models import Item, ItemTransfer, AmountMeasure, Location, ItemType
from lims.inventory.serializers import ItemTransferPreviewSerializer
from .models import (Workflow, ActiveWorkflow, WorkflowProduct, DataEntry,
                     TaskTemplate, InputFieldTemplate)
from .serializers import (WorkflowSerializer, SimpleTaskTemplateSerializer,
                          TaskTemplateSerializer, ActiveWorkflowSerializer,
                          DetailedActiveWorkflowSerializer, TaskValuesSerializer,
                          InputFieldTemplateSerializer)


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    Provide a list of workflow templates that are available.

    ### query_params

    - _search_: search workflow name and created_by
    """
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    search_fields = ('name', 'created_by__username',)
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)

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


class ActiveWorkflowViewSet(viewsets.ModelViewSet):
    """
    Provide a list of all workflows in progress.
    """
    queryset = ActiveWorkflow.objects.all()
    serializer_class = ActiveWorkflowSerializer
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedActiveWorkflowSerializer
        return self.serializer_class

    def destroy(self, request, *args, **kwargs):
        """
        Clean up all "products" on this workflow when deleted
        """
        for s in self.get_object().product_statuses.all():
            s.delete()
        return super(ActiveWorkflowViewSet, self).destroy(self, request, *args, **kwargs)

    @detail_route(methods=['POST'])
    def add_product(self, request, pk=None):
        """
        Add a product to the specified active workflow

        ### query_params

        - _id_ (**required**): An ID of a valid _Product_
        """
        product_id = request.query_params.get('id', None)
        workflow = self.get_object()
        if product_id:
            try:
                s = Product.objects.get(pk=product_id)
            except ObjectDoesNotExist:
                return Response({
                    'message': 'Product with the id {} does not exist'
                    .format(product_id)}, status=404)
            ws = WorkflowProduct(product=s)
            ws.save()
            workflow.product_statuses.add(ws)
            return Response(status=201)
        return Response({'message': 'You must provide a product ID'}, status=400)

    @detail_route(methods=['POST'])
    def remove_product(self, request, pk=None):
        """
        Remove a product from the active workflow

        ### query_params

        - _id_ (**required**): An ID of a valid _WorkflowProduct_
        """
        workflow_product_id = request.query_params.get('id', None)
        self.get_object()
        if workflow_product_id:
            try:
                ws = WorkflowProduct.objects.get(pk=workflow_product_id)
            except ObjectDoesNotExist:
                return Response({
                    'message': 'Workflow product with the id {} does not exist'
                    .format(workflow_product_id)}, status=404)
            current_workflow = ws.activeworkflow.all()[0]
            ws.delete()
            if current_workflow.product_statuses.count() == 0:
                current_workflow.delete()
            return Response(status=201)
        return Response({'message': 'You must provide a workflow product ID'}, status=400)

    @detail_route(methods=['POST'])
    def switch_workflow(self, request, pk=None):
        """
        Switch a product to another workflow from the active workflow

        Can either switch to an existing workflow or create a new workflow
        with this _WorkflowProduct_ on.

        ### query_params

        - _id_ (**required**): An ID of a valid _WorkflowProduct_
        - _workflow_id_ (**or**): An ID of the _Workflow_ you want to switch to
        - _active_workflow_id_ (**or**): An ID of an existing _ActiveWorkflow_ to switch to
        """
        workflow_product_id = request.query_params.get('id', None)
        new_workflow_id = request.query_params.get('workflow_id', None)
        existing_workflow_id = request.query_params.get('active_workflow_id', None)
        self.get_object()
        if workflow_product_id and (new_workflow_id or existing_workflow_id):
            try:
                ws = WorkflowProduct.objects.get(pk=workflow_product_id)
            except ObjectDoesNotExist:
                return Response({
                    'message': 'Workflow product with the id {} does not exist'
                    .format(workflow_product_id)}, status=404)

            current_workflow = ws.activeworkflow.all()[0]

            if existing_workflow_id:
                try:
                    aw = ActiveWorkflow.objects.get(pk=existing_workflow_id)
                except ObjectDoesNotExist:
                    return Response({
                        'message': 'Active workflow with the id {} does not exist'
                        .format(existing_workflow_id)}, status=404)
                current_workflow.products.remove(ws)
                aw.products.add(ws)
            else:
                try:
                    nw = Workflow.objects.get(pk=new_workflow_id)
                except ObjectDoesNotExist:
                    return Response({
                        'message': 'Workflow with the id {} does not exist'
                        .format(new_workflow_id)}, status=404)
                naw = ActiveWorkflow(
                    workflow=nw,
                    started_by=request.user)
                naw.save()
                naw.product_statuses.add(ws)
                current_workflow.products.remove(ws)

            if current_workflow.product_statuses.count() == 0:
                current_workflow.delete()
            return Response(status=201)
        return Response({'message': 'You must provide a workflow product ID'}, status=400)

    def update_item_amounts(self, identifier, amount, measure, required_amounts, ureg):
        """
        Utility function to avoid repetition when updating amounts.
        """
        if identifier in required_amounts:
            try:
                required_amounts[identifier] += float(amount) * ureg(measure)
            except UndefinedUnitError:
                required_amounts[identifier] += float(amount)
        else:
            try:
                required_amounts[identifier] = float(amount) * ureg(measure)
            except UndefinedUnitError:
                required_amounts[identifier] = float(amount)

    @detail_route(methods=['POST'])
    def start_task(self, request, pk=None):
        """
        Start a task creating data entry and removing from inventory.

        Takes in task data, serializes for use in the data entry
        and takes the relevant amounts from the inventory.

        Can also act in preview mode and just return the info
        required for the task.

        ### query_params

        - _is_preview_: Don't actually start the task, just return
                        the task information.

        ### query data

        - _task_ (**required**): A JSON representation of the task to be serialized
        - _products_ (**required**): A list of product ID's that are a part of the task
        - _input_files_: A list of file contents to be used as input for the task
        """
        task_data = json.loads(self.request.data.get('task', None))
        task_serializer = TaskValuesSerializer(data=task_data)

        product_data = json.loads(self.request.data.get('products', []))
        file_data = self.request.data.getlist('input_files', [])

        is_preview = request.query_params.get('is_preview', False)

        active_workflow = self.get_object()
        uuid = uuid4()
        ureg = UnitRegistry()

        # This takes each input file and merges all rows with
        # matching identifiers into a single dict.
        # This will overwrite duplicated entries with the last
        # file processed, which is why values should only be
        # defined in a single file.
        input_file_data = {}
        for f in file_data:
            try:
                ft = FileTemplate.objects.get(name=f.name)
            except:
                pass
            else:
                parsed_file = ft.read(TextIOWrapper(f.file, encoding=f.charset))
                if parsed_file:
                    for key, row in parsed_file.items():
                        if key not in input_file_data:
                            input_file_data[key] = {}
                        input_file_data[key].update(row)
                else:
                    return Response(
                        {'message':
                         'Input file "{}" has incorrect headers/format'.format(f.name)},
                        status=400)

        products = Product.objects.filter(id__in=[p['product'] for p in product_data])

        if task_serializer.is_valid(raise_exception=True) and len(products) > 0:
            # A dict of items and amounts required from inputs
            required_amounts = {}
            input_items = []
            fields_from_file = []
            data_items = {}

            # Look for items for use as inputs to the task and add the amounts that are required to the list
            for prd in products:
                items = Item.objects.filter(
                    products__id=prd.id, item_type__name=task_data['product_input'])
                if items.count() == 0:
                    return Response(
                        {'message':
                         '{}: {} does not contain any items to use as input'.format(
                             prd.product_identifier, prd.name)}, status=400)
                input_items.extend(items)

                # Add items from Product's to the list
                for itm in items:
                    identifier = frozenset([prd.product_identifier, itm.identifier])
                    data_items[identifier] = {
                        'data': task_serializer.data,
                        'product': prd,
                        'item': itm
                    }
                    self.update_item_amounts(itm.identifier,
                                             task_serializer.data['product_input_amount'],
                                             task_serializer.data['product_input_measure'],
                                             required_amounts, ureg)

            # Look through any input files for matching identifiers and add their amounts to the list
            for key, row in input_file_data.items():
                for header, value in row.items():
                    # If the header has identifier/amount combo then
                    # is aplicable to an item in the product
                    # if not, it is applicable TO the product
                    exists = False
                    matched_headers = []
                    label = header.rstrip(' identifier').rstrip(' amount')
                    # Look for _amount + _identifier combos and math them up
                    if header.endswith('identifier') and header not in matched_headers:
                        identifier = value
                        amount_field_name = '{} amount'.format(label)
                        if amount_field_name in row.keys():
                            amount = row[amount_field_name]
                            matched_headers.extend([header, amount_field_name])
                            exists = True
                    elif header.endswith('amount') and header not in matched_headers:
                        identifier_field_name = '{} identifier'.format(label)
                        if identifier_field_name in row.keys():
                            identifier = row[identifier_field_name]
                            amount = value
                            matched_headers.extend([header, identifier_field_name])
                            exists = True
                        elif identifier_field_name not in row.keys() and header in row.keys():
                            # This value is directly for an amount on the item
                            # rather than another input
                            identifier = key[1]
                            amount = value
                            label = header.replace(' ', '_')
                            measure_label = label.replace('amount', 'measure')
                            matched_headers.append(header)
                            exists = True
                    if exists:

                        # Look for the matching pairs
                        try:
                            data_entry_field = next((fld for fld in data_items[key]['data'][
                                                    'input_fields'] if fld['label'] == label))
                            data_entry_field['amount'] = amount
                            measure = data_entry_field['measure']
                        except StopIteration:
                            data_items[key]['data'][label] = amount
                            measure = data_items[key]['data'][measure_label]

                        # Try to get the item from the inventory and add to list
                        try:
                            ti = Item.objects.get(identifier=identifier)
                        except ObjectDoesNotExist:
                            return Response(
                                {'message':
                                 '{} does not exist in the inventory'.format(identifier)},
                                status=400)
                        if ti not in input_items:
                            input_items.append(ti)
                        self.update_item_amounts(ti.identifier, amount,
                                                 measure, required_amounts, ureg)

                        # Record this field has data from a file and does not need to be processed again
                        fields_from_file.append(label)

            # Now just read through the fields left and fill in any more details
            for itm in task_serializer.data['input_fields']:
                # If we already have set the value in a file we don't want to overwrite it
                if itm['label'] not in fields_from_file and itm['from_input_file'] == False:
                    try:
                        ti = Item.objects.get(identifier=itm['inventory_identifier'])
                    except ObjectDoesNotExist:
                        return Response({'message': '{} does not exist in the inventory'.format(
                            itm['inventory_identifier'])}, status=400)
                    if ti not in input_items:
                        input_items.append(ti)
                    self.update_item_amounts(ti.identifier, itm['amount'], itm[
                                             'measure'], required_amounts, ureg)
                # But if it's suposed to have been from a file and is still here, return an error
                elif itm['label'] not in fields_from_file and itm['from_input_file'] == True:
                    return Response({'message': 'The value for field "{}" is not present in file'.format(itm['label'])}, status=400)

            # input checks
            preview_data = []
            valid_amounts = True
            amount_error_messages = []
            for item in input_items:
                # Check enough of each item is avilable.
                # First, translate to a known amount (if possible) or just be presented as a raw number
                try:
                    available = item.amount_available * ureg(item.amount_measure.symbol)
                except UndefinedUnitError:
                    available = item.amount_available
                required = required_amounts[item.identifier]
                # The actual check
                if available < required:
                    missing = (available - required_amounts[item.identifier]) * -1
                    valid_amounts = False
                    amount_error_messages.append(
                        'Inventory item {} ({}) is short of amount by {}'.format(
                            item.identifier, item.name, missing))

                # If it's a preview then just serialize the amount, don't actually do anything with it
                if is_preview:
                    amount = required_amounts[item.identifier]
                    amount_symbol = '{:~}'.format(amount).split(' ')[1]
                    item_transfer = ItemTransfer(
                        item=item,
                        amount_taken=amount.magnitude,
                        amount_measure=AmountMeasure.objects.get(symbol=amount_symbol)
                    )
                    sit = ItemTransferPreviewSerializer(item_transfer)
                    preview_data.append(sit.data)

            if not is_preview:
                # If valid, continue to create item transfers
                if valid_amounts:
                    for item in input_items:
                        # Create item transfers
                        amount = required_amounts[item.identifier]
                        amount_symbol = '{:~}'.format(amount).split(' ')[1]
                        item_transfer = ItemTransfer(
                            item=item,
                            run_identifier=uuid,
                            amount_taken=amount.magnitude,
                            amount_measure=AmountMeasure.objects.get(symbol=amount_symbol)
                        )
                        item_transfer.save()

                        # Alter amounts in DB to corrospond to the amount taken
                        new_amount = available - required_amounts[item.identifier]
                        item.amount_available = new_amount.magnitude
                        item.save()
                else:
                    return Response({'message': '\n'.join(amount_error_messages)}, status=400)

                # make data entries to record the values of the task
                task = TaskTemplate.objects.get(pk=task_data['id'])
                for key, data in data_items.items():
                    entry = DataEntry(
                        run_identifier=uuid,
                        product=data['product'],
                        item=data['item'],
                        created_by=self.request.user,
                        state='active',
                        data=data['data'],
                        workflow=active_workflow.workflow,
                        task=task
                    )
                    entry.save()

                    # update products that task started
                    active = WorkflowProduct.objects.get(product=data['product'])
                    active.task_in_progress = True
                    active.run_identifier = uuid
                    active.save()

                return Response({'message': 'Task started'})
            return Response(preview_data)
        return Response({'message': 'You must provide task data and products'}, status=400)

    @detail_route(methods=['GET'])
    def task_status(self, request, pk=None):
        """
        Get information on a task that is being run.

        Provides a dict of values matching what was sent to the task.

        ### query_params

        - _run_identifier_ (**required**): The run identifier generated when starting the task
        - _task_number_ (**required**): The number of the current task being run
        """
        run_identifier = self.request.query_params.get('run_identifier', None)
        task_number = self.request.query_params.get('task_number', None)

        if run_identifier and task_number:
            active_products = self.get_object().product_statuses.filter(
                run_identifier=run_identifier, current_task=task_number)
            product_ids = [ap.product.id for ap in active_products]

            data_items = DataEntry.objects.filter(
                product__id__in=product_ids, run_identifier=run_identifier).order_by('product__id')

            if data_items.count() > 0:
                response_data = {
                    'name': data_items[0].task.name,
                    'items': {}
                }

                table = []
                for d in data_items:
                    td = {
                        'id': d.product.id,
                        'product_name':
                            '{}: {}'.format(d.product.product_identifier, d.product.name),
                        'item_name': '{}: {}'.format(d.item.identifier, d.item.name),
                        'fields': [],
                    }
                    td['fields'].append({
                        'label': 'Task input',
                        'value':
                            '{} {} {}'.format(
                                d.data['product_input'],
                                d.data['product_input_amount'], d.data['product_input_measure'])
                    })
                    for ip in d.data['input_fields']:
                        td['fields'].append({
                            'label': ip['label'],
                            'value':
                                '{} {} {}'.format(
                                    ip['inventory_identifier'], ip['amount'], ip['measure'])
                        })
                    table.append(td)
                table.sort(key=itemgetter('product_name'))
                response_data['items'] = {k: list(g) for k, g in groupby(
                    table, itemgetter('product_name'))}
                return Response(response_data)
            return Response({'message': 'Task complete'}, status=410)
        return Response(
            {'message': 'You must provide the number of the task and a run identifier'}, status=400)

    def _update_products(self, task_id, products, activeworkflow, request, retry=False):
        """
        Utility function to update products at end of task.
        """
        task_list = activeworkflow.workflow.order.split(',')

        for p in products:
            data_entries = DataEntry.objects.filter(run_identifier=p.run_identifier)
            created_from_items = []
            for entry in data_entries:
                created_from_items.append(entry.item)
                if retry:
                    entry.state = 'failed'
                else:
                    entry.state = 'succeeded'
                entry.save()

            # Make outputs
            # This requires an ItemTransfer to also be created
            for output in data_entries[0].data['output_fields']:
                item_type = ItemType.objects.get(name=output['lookup_type'])
                measure = AmountMeasure.objects.get(symbol=output['measure'])
                location = Location.objects.get(name='Lab')
                output_item = Item(
                    name='{} {}'.format(p.product_identifier(), output['lookup_type']),
                    identifier='{}OPT{}'.format(p.product_identifier(), datetime.datetime.now()),
                    item_type=item_type,
                    in_inventory=True,
                    amount_available=float(output['amount']),
                    amount_measure=measure,
                    location=location,
                    added_by=request.user,
                )
                output_item.save()

                output_item.created_from.add(*created_from_items)

                # We want to add it to history but say it is
                # and addition rather than a subtraction
                tsf = ItemTransfer(
                    item=output_item,
                    amount_taken=float(output['amount']),
                    amount_measure=measure,
                    run_identifier=p.run_identifier,
                    is_addition=True,
                )
                tsf.save()

            p.run_identifier = ''
            p.task_in_progress = False

            p.save()
            if not retry:
                if p.current_task + 1 < len(task_list):
                    p.current_task += 1
                    p.save()
                else:
                    p.delete()

    @detail_route(methods=['POST'])
    def complete_task(self, request, pk=None):
        """
        Complete a task and incrementing the current_task value

        This will mark all data entries as successful, create output items
        and then increment the current_task value.

        ### query data

        - (**required**): A list of product id's to mark as complete
        """
        product_ids = request.data
        activeworkflow = self.get_object()

        if len(product_ids) > 0:
            products = activeworkflow.product_statuses.filter(product__id__in=product_ids)

            # Update item transfers to indicate now complete
            item_transfers = ItemTransfer.objects.filter(run_identifier=products[0].run_identifier)
            item_transfers.update(transfer_complete=True)

            self._update_products(products[0].current_task, products, activeworkflow, request)

            # If there are no more products left on the workflow, complete it.
            if activeworkflow.product_statuses.count() == 0:
                activeworkflow.delete()
                return Response({'message': 'Workflow has been completed'}, status=410)
            else:
                activeworkflow.save()
            return Response({'message': 'Task is complete'})
        return Response({'message': 'You must provide product IDs'}, status=400)

    @detail_route(methods=['POST'])
    def retry_task(self, request, pk=None):
        """
        Complete a task without incrementing the current_task value

        This will mark all data entries as failed and clear the products
        ready for a retry.

        ### query data

        - (**required**): A list of product id's to mark as complete
        """
        product_ids = request.data
        activeworkflow = self.get_object()

        if len(product_ids) > 0:
            products = activeworkflow.product_statuses.filter(product__id__in=product_ids)
            self._update_products(products[0].current_task, products,
                                  activeworkflow, request, retry=True)

            # Update item transfers to indicate now complete
            item_transfers = ItemTransfer.objects.filter(run_identifier=products[0].run_identifier)
            item_transfers.update(transfer_complete=True)

            return Response({'message': 'Task ready for retry'})
        return Response({'message': 'You must provide product IDs'}, status=400)


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


class TaskViewSet(viewsets.ModelViewSet):
    """
    Provide a list of TaskTemplates available
    """
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)
    search_fields = ('name', 'created_by__username', )
    filter_class = TaskFilterSet

    def retrieve(self, request, pk=None):
        # Do any calculations before sending the task data
        instance = self.get_object()
        serializer = self.get_serializer(instance)  # self.get_task(pk)
        return Response(serializer.data)

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
                return Response(serializer.data)
        serializer = TaskTemplateSerializer(obj)
        return Response(serializer.data)


class TaskFieldViewSet(viewsets.ModelViewSet):
    """
    Provides a list of all task fields
    """
    ordering_fields = ('name',)

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
