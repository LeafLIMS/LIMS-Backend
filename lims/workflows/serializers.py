from django.db import models
from django.contrib.auth.models import User

from rest_framework.fields import *
from rest_framework import serializers

from lims.equipment.models import Equipment
from lims.filetemplate.models import FileTemplate
from lims.inventory.models import Item, ItemType, AmountMeasure 
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
    product_identifier = serializers.CharField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    product_project = serializers.IntegerField(read_only=True)
    class Meta:
        model = WorkflowProduct

class ActiveWorkflowSerializer(serializers.ModelSerializer):
    """
    Provides a basic serialisation of active workflow data
    """
    workflow_data = WorkflowSerializer(read_only=True, source='workflow')
    started_by = serializers.SlugRelatedField(
        queryset = User.objects.all(),
        slug_field = 'username'
    )
    class Meta:
        model = ActiveWorkflow

class DetailedActiveWorkflowSerializer(serializers.ModelSerializer):
    """
    Provides a more detailed serialisation of active workflows
    """
    product_statuses = WorkflowProductSerializer(read_only=True, many=True)
    workflow_name = serializers.CharField(read_only=True)
    class Meta:
        model = ActiveWorkflow

class DataEntrySerializer(serializers.ModelSerializer):
    workflow = serializers.SlugRelatedField(
            queryset = Workflow.objects.all(),
            slug_field = 'name'
            )
    task = serializers.SlugRelatedField(
            queryset = TaskTemplate.objects.all(),
            slug_field = 'name'
            )
    item = serializers.SlugRelatedField(
            queryset = Item.objects.all(),
            slug_field = 'name'
            )
    class Meta:
        model = DataEntry

class InputFieldTemplateSerializer(serializers.ModelSerializer):
    measure = serializers.SlugRelatedField(
            queryset = AmountMeasure.objects.all(),
            slug_field = 'symbol'
            )
    lookup_type = serializers.SlugRelatedField(
            queryset = ItemType.objects.all(),
            slug_field = 'name'
            )
    field_name = serializers.CharField(read_only=True)
    store_value_in = serializers.CharField(read_only=True)
    class Meta:
        model = InputFieldTemplate

class InputFieldValueSerializer(serializers.Serializer):
    """
    Serializes the values from an input field
    """
    label = serializers.CharField()
    amount = serializers.FloatField()
    measure = serializers.CharField()
    inventory_identifier = serializers.CharField()

class VariableFieldTemplateSerializer(serializers.ModelSerializer):
    measure = serializers.SlugRelatedField(
            allow_null = True,
            required = False, 
            queryset = AmountMeasure.objects.all(),
            slug_field = 'symbol'
            )
    field_name = serializers.CharField(read_only=True)
    class Meta:
        model = VariableFieldTemplate

class VariableFieldValueSerializer(serializers.Serializer):
    """
    Serializes the values from an input field
    """
    label = serializers.CharField()
    amount = serializers.FloatField()
    measure = serializers.CharField(required=False, allow_null=True)

class OutputFieldTemplateSerializer(serializers.ModelSerializer):
    measure = serializers.SlugRelatedField(
            queryset = AmountMeasure.objects.all(),
            slug_field = 'symbol'
            )
    lookup_type = serializers.SlugRelatedField(
            queryset = ItemType.objects.all(),
            slug_field = 'name'
            )
    field_name = serializers.CharField(read_only=True)
    class Meta:
        model = OutputFieldTemplate

class OutputFieldValueSerializer(serializers.Serializer):
    """
    Serializes the values from an input field
    """
    label = serializers.CharField()
    amount = serializers.FloatField()
    measure = serializers.CharField()
    lookup_type = serializers.CharField()

class CalculationFieldTemplateSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField()
    class Meta:
        model = CalculationFieldTemplate

class CalculationFieldValueSerializer(serializers.Serializer):
    """
    Serializes the values from an input field
    """
    label = serializers.CharField()
    calculation = serializers.CharField()

class StepFieldPropertySerializer(serializers.ModelSerializer):
    measure = serializers.SlugRelatedField(
            queryset = AmountMeasure.objects.all(),
            slug_field = 'symbol'
            )
    field_name = serializers.CharField(read_only=True)
    class Meta:
        model = StepFieldProperty
        fields = ('id', 'measure', 'amount', 'label', 'from_calculation', 'calculation_used', 'field_name',)  

class StepFieldPropertyValueSerializer(serializers.Serializer):
    """
    Serializes the values from an input field
    """
    label = serializers.CharField()
    amount = serializers.FloatField()
    measure = serializers.CharField()

class StepFieldTemplateSerializer(serializers.ModelSerializer):
    properties = StepFieldPropertySerializer(many=True)
    field_name = serializers.CharField(read_only=True)
    class Meta:
        model = StepFieldTemplate

    def create(self, validated_data):
        property_fields = validated_data.pop('properties')
        step = StepFieldTemplate.objects.create(**validated_data)
        for field in property_fields:
            StepFieldProperty.objects.create(step=step, **field)
        return step 

    def update(self, instance, validated_data):
        properties_data = validated_data.pop('properties')
        
        properties = instance.properties

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        property_ids = [item['id'] for item in properties_data]
        for field in properties:
            if field.id not in property_ids:
                field.delete()

        for field in properties_data:
            field = StepFieldProperty(step=instance, **field)
            field.save()

        return instance

class StepFieldValueSerializer(serializers.Serializer):
    label = serializers.CharField()
    properties = StepFieldPropertyValueSerializer(many=True)

class TaskTemplateSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
            queryset = User.objects.filter(is_staff=True),
            slug_field = 'username'
            )
    product_input = serializers.SlugRelatedField(
            queryset = ItemType.objects.all(),
            slug_field = 'name'
            )
    product_input_measure = serializers.SlugRelatedField(
            queryset = AmountMeasure.objects.all(),
            slug_field = 'symbol'
            )
    labware = serializers.SlugRelatedField(
            queryset = ItemType.objects.all(),
            slug_field = 'name'
            )
    capable_equipment = serializers.SlugRelatedField(
            many = True,
            queryset = Equipment.objects.all(),
            slug_field = 'name'
            )
    input_files = serializers.SlugRelatedField(
            many = True,
            queryset = FileTemplate.objects.all(),
            slug_field = 'name'
            )
    output_files = serializers.SlugRelatedField(
            many = True,
            queryset = FileTemplate.objects.all(),
            slug_field = 'name'
            )
    input_fields = InputFieldTemplateSerializer(read_only=True, many=True) 
    variable_fields = VariableFieldTemplateSerializer(read_only=True, many=True) 
    calculation_fields = CalculationFieldTemplateSerializer(read_only=True, many=True) 
    output_fields = OutputFieldTemplateSerializer(read_only=True, many=True) 
    step_fields = StepFieldTemplateSerializer(read_only=True, many=True) 
    store_labware_as = serializers.CharField(read_only=True)
    class Meta:
        model = TaskTemplate

class SimpleTaskTemplateSerializer(TaskTemplateSerializer):
    class Meta:
        model = TaskTemplate
        fields = ('id', 'name', 'description', 'product_input', 'capable_equipment', 'created_by', 'date_created',)

class TaskValuesSerializer(serializers.Serializer):
    product_input = serializers.CharField() 
    product_input_amount = serializers.FloatField() 
    product_input_measure = serializers.CharField()
    labware_identifier = serializers.CharField()
    input_fields = InputFieldValueSerializer(many=True) 
    variable_fields = VariableFieldValueSerializer(many=True) 
    calculation_fields = CalculationFieldValueSerializer(many=True) 
    output_fields = OutputFieldValueSerializer(many=True) 
    step_fields = StepFieldValueSerializer(many=True) 
