import inspect
import pprint
from operator import itemgetter

from collections import OrderedDict

from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.utils.enclimsg import force_text

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.metadata import SimpleMetadata
from rest_framework.permissions import IsAdminUser, DjangoObjectPermissions

from rest_framework.utils.field_mapping import ClassLookupDict

import lims.workflows.models as AvailableModels
from lims.projects.models import Product
from .models import Workflow, ActiveWorkflow, WorkflowProduct, DataEntry, TaskTemplate
from .serializers import *

class TaskMixin:
    def get_task(self, pk):
        model = TaskTemplate.objects.get_subclass(pk=pk)
        serializer_name = model.__class__.__name__ + 'Serializer'
        serializer_class = globals()[serializer_name]
        serializer = serializer_class(model)
        return serializer

    def get_serializer_class_from_name(self, name):
        serializer_name = name + 'Serializer'
        serializer_class = globals()[serializer_name]
        return serializer_class

class WorkflowViewSet(viewsets.ModelViewSet):
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
            serializer_name = t.__class__.__name__ + 'Serializer'
            serializer_class = globals()[serializer_name]
            serializer_task = serializer_class(t)
            tasklist.append(serializer_task.data)
        result['tasks'] = tasklist;
        return Response(result)

    @detail_route()
    def task_details(self, request, pk=None):
        workflow = self.get_object()
        position = request.query_params.get('position', None)
        if position:
            try:
                taskId = workflow.order.split(',')[int(position)] 
                task = TaskTemplate.objects.get(pk=taskId)
                task.handle_calculations()
                serializer = TaskTemplateSerializer(task) 
                result = serializer.data
            except IndexError:
                return Response({'message': 'Invalid position'}, status=400)
            except ObjectDoesNotExist:
                return Response({'message': 'Task does not exist'}, status=400)
            return Response(result)
        return Response({'message': 'Please provide a task position'}, status=400)

class ActiveWorkflowViewSet(viewsets.ModelViewSet, TaskMixin):
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
        for s in self.get_object().products.all():
            s.delete()
        return super(ActiveWorkflowViewSet, self).destroy(self, request, *args, **kwargs)

    @detail_route(methods=['POST'])
    def add_product(self, request, pk=None):
        """
        Add a product to the active workflow
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
            workflow.products.add(ws)
            return Response(status=201)
        return Response({'message': 'You must provide a product ID'}, status=400)

    @detail_route(methods=['POST'])
    def remove_product(self, request, pk=None):
        """
        Remove a product from the active workflow
        """
        workflow_product_id = request.query_params.get('id', None)
        workflow = self.get_object()
        if workflow_product_id:
            try:
                ws = WorkflowProduct.objects.get(pk=workflow_product_id)
            except ObjectDoesNotExist:
                return Response({
                    'message': 'Workflow product with the id {} does not exist'
                    .format(workflow_product_id)}, status=404)
            current_workflow = ws.activeworkflow.all()[0]
            ws.delete()
            if current_workflow.products.count() == 0:
                current_workflow.delete()    
            return Response(status=201)
        return Response({'message': 'You must provide a workflow product ID'}, status=400)

    @detail_route(methods=['POST'])
    def switch_workflow(self, request, pk=None):
        """
        Switch a product to another workflow from the active workflow
        """
        workflow_product_id = request.query_params.get('id', None)
        new_workflow_id = request.query_params.get('workflow_id', None)
        existing_workflow_id = request.query_params.get('active_workflow_id', None)
        workflow = self.get_object()
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
                naw.products.add(ws)
                current_workflow.products.remove(ws)

            if current_workflow.products.count() == 0:
                current_workflow.delete()    
            return Response(status=201)
        return Response({'message': 'You must provide a workflow product ID'}, status=400)

    @detail_route()
    def tasks(self, request, pk=None):
        tasklist = []
        tasks = self.get_object().workflow.get_tasks()
        for t in tasks:
            serializer_class = self.get_serializer_class_from_name(t.__class__.__name__)
            serializer = serializer_class(t)
            tasklist.append(serializer.data)
        return Response(tasklist)

    @detail_route(methods=['POST'])
    def start_task(self, request, pk=None):
        """
        Mark a task started for a given product
        ---
        parameters_strategy: replace
        parameters:
            - name: pk
              required: true
              paramType: path
            - name: id
              required: true
              paramType: query
        """
        workflow_product = request.query_params.get('id', None)
        if workflow_product:
            try:
                ws = WorkflowProduct.objects.get(pk=workflow_product)
            except ObjectDoesNotExist:
                return Response({'message': 'Workflow product does not exist'}, status=404)
            ws.task_in_progress = True
            ws.save()
            #TODO: Generation of files for equipment
            # The locations can be returned in the response
            return Response({'message': 'Task is now active'})
        return Response({'message': 'You must provide a workflow product ID'}, status=400)

    def _update_products(self, task_id, components, activeworkflow, request, retry=False):
        task_list = activeworkflow.workflow.order.split(',')
        try:
            task = TaskTemplate.objects.get(pk=task_id)
        except:
            return Response({'message': 'Task does not exist'}, status=404)

        groupedEntries = {}
        for element in components:
            if element['productId'] not in groupedEntries.keys():
                groupedEntries[element['productId']] = []
            groupedEntries[element['productId']].append(element)

        for product_id, group in groupedEntries.items():
            product = WorkflowProduct.objects.get(product__id=product_id)
            for c in group:
                entry = DataEntry(
                    product=product.product,
                    created_by=request.user,
                    workflow=activeworkflow.workflow,
                    state='succeded',
                    data=c,
                    task=task
                )
                
                if retry:
                    entry.state = 'failed'

                entry.save()

            if not retry:
                if product.current_task + 1 < len(task_list):
                    product.current_task += 1
                    product.save()
                else:
                    product.delete()

    @detail_route(methods=['POST'])
    def complete_task(self, request, pk=None):
        """
        Complete a task, storing results and setting the next task
        """
        task_id = request.query_params.get('taskId', None)
        components = request.data;

        if components and task_id:
            activeworkflow = self.get_object()
            self._update_products(task_id, components, activeworkflow, request)
            if activeworkflow.products.count() == 0:
                activeworkflow.delete()
                return Response({'message': 'Workflow has been completed'}, status=410)
            else:
                activeworkflow.saved = None
                activeworkflow.save()
            return Response({'message': 'Task is complete'})
        return Response({'message': 'You must provide a taskId and data'}, status=400)

    @detail_route(methods=['POST'])
    def retry_task(self, request, pk=None):
        """
        Retry a task, storing results and indicating cleared.
        """
        task_id = request.query_params.get('taskId', None)
        components = request.data;

        if components and task_id:
            activeworkflow = self.get_object()
            self._update_products(task_id, components, activeworkflow, request, retry=True)
            return Response({'message': 'Task information recorded', 'retry': True})
        return Response({'message': 'You must provide a taskId and data'}, status=400)

class TaskViewSet(viewsets.ModelViewSet, TaskMixin):
    queryset = TaskTemplate.objects.all().select_subclasses()
    serializer_class = TaskTemplateSerializer
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)
    search_fields = ('name', 'created_by__username',)

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        instance.handle_calculations();
        serializer = self.get_serializer(instance) #self.get_task(pk)
        return Response(serializer.data)

    @detail_route(methods=["POST"])
    def recalculate(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        fields = request.data.get('fields', None)
        if fields: 
            obj.fields = request.data.get('fields')
            obj.handle_calculations()
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        return Response(serializer.data)

    @list_route(methods=["POST"])
    def create_task(self, request):
        task_type = request.query_params.get('type', None)
        if task_type:
            serializer_class = self.get_serializer_class(task_type)
            serializer = serializer_class(request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data)
        return Response({'message': 'Please supply a type of task to create'}, status=400)

class TaskFieldViewset(viewsets.ModelViewSet, TaskMixin):
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)

    def get_serializer_class(self):
        type_name = self.request.query_params.get('type', None)
        if type_name:
            serializer_name = type_name + 'FieldTemplateSerializer'
            serializer_class = globals()[serializer_name]
            return serializer_class 
        return None
    
    def get_queryset(self):
        type_name = self.request.query_params.get('type', None)
        if type_name:
            object_name = type_name + 'FieldTemplate'
            object_class = globals()[name]
            return object_class 
        return None
