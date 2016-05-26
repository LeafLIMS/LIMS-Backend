from django.db import models
from django.contrib.auth.models import User

from rest_framework.fields import *
from rest_framework import serializers

from lims.inventory.models import ItemType 
from lims.projects.serializers import ProductSerializer
from .models import (Workflow, ActiveWorkflow, DataEntry, 
    TaskTemplate, WorkflowProduct, InputFieldTemplate, VariableFieldTemplate,
    OutputFieldTemplate, CalculationFieldTemplate, StepFieldTemplate, 
    StepFieldProperty)

class WorkflowSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
            queryset = User.objects.all(),
            slug_field = 'username'
            )
    class Meta:
        model = Workflow

class WorkflowProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True) 
    class Meta:
        model = WorkflowProduct

class ActiveWorkflowSerializer(serializers.ModelSerializer):
    workflow_data = WorkflowSerializer(read_only=True, source='workflow')
    started_by = serializers.SlugRelatedField(
        queryset = User.objects.all(),
        slug_field = 'username'
    )
    class Meta:
        model = ActiveWorkflow

class DetailedActiveWorkflowSerializer(serializers.ModelSerializer):
    products = WorkflowProductSerializer(read_only=True, many=True)
    workflow_name = serializers.CharField(read_only=True)
    class Meta:
        model = ActiveWorkflow

class DataEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataEntry

class TaskTemplateSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
            queryset = User.objects.filter(is_staff=True),
            slug_field = 'username'
            )
    product_input = serializers.SlugRelatedField(
            queryset = ItemType.objects.all(),
            slug_field = 'name'
            )
    class Meta:
        model = TaskTemplate

class InputFieldTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InputFieldTemplate

class VariableFieldTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableFieldTemplate

class OutputFieldTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutputFieldTemplate

class CalculationFieldTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationFieldTemplate

class StepFieldTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepFieldTemplate

class StepFieldPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = StepFieldProperty
