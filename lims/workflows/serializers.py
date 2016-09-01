import re

from rest_framework import serializers
from pyparsing import ParseException

from lims.permissions.permissions import (SerializerPermissionsMixin,
                                          SerializerReadOnlyPermissionsMixin)

from lims.equipment.models import Equipment
from lims.filetemplate.models import FileTemplate
from lims.inventory.models import Item, ItemType, AmountMeasure
from .models import (Workflow, ActiveWorkflow, DataEntry,
                     TaskTemplate, WorkflowProduct, InputFieldTemplate, VariableFieldTemplate,
                     OutputFieldTemplate, CalculationFieldTemplate, StepFieldTemplate,
                     StepFieldProperty)
from .calculation import NumericStringParser


class WorkflowSerializer(SerializerPermissionsMixin, serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Workflow


class WorkflowProductSerializer(SerializerReadOnlyPermissionsMixin, serializers.ModelSerializer):
    product_identifier = serializers.CharField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    product_project = serializers.IntegerField(read_only=True)
    has_task_inputs = serializers.BooleanField(read_only=True)

    class Meta:
        model = WorkflowProduct


class ActiveWorkflowSerializer(SerializerReadOnlyPermissionsMixin, serializers.ModelSerializer):
    """
    Provides a basic serialisation of active workflow data
    """
    workflow_data = WorkflowSerializer(read_only=True, source='workflow')
    started_by = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
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
        queryset=Workflow.objects.all(),
        slug_field='name'
    )
    task = serializers.SlugRelatedField(
        queryset=TaskTemplate.objects.all(),
        slug_field='name'
    )
    item = serializers.SlugRelatedField(
        queryset=Item.objects.all(),
        slug_field='name'
    )

    class Meta:
        model = DataEntry


class InputFieldTemplateSerializer(serializers.ModelSerializer):
    measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(),
        slug_field='symbol'
    )
    lookup_type = serializers.SlugRelatedField(
        queryset=ItemType.objects.all(),
        slug_field='name'
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
    from_input_file = serializers.NullBooleanField()


class VariableFieldTemplateSerializer(serializers.ModelSerializer):
    measure = serializers.SlugRelatedField(
        allow_null=True,
        required=False,
        queryset=AmountMeasure.objects.all(),
        slug_field='symbol'
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
        queryset=AmountMeasure.objects.all(),
        slug_field='symbol'
    )
    lookup_type = serializers.SlugRelatedField(
        queryset=ItemType.objects.all(),
        slug_field='name'
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
    field_name = serializers.CharField(read_only=True)

    class Meta:
        model = CalculationFieldTemplate


class CalculationFieldIDTemplateSerializer(CalculationFieldTemplateSerializer):
    """
    Used for when an ID is also needed
    """
    id = serializers.IntegerField()


class CalculationFieldValueSerializer(serializers.Serializer):
    """
    Serializes the values from an input field
    """
    label = serializers.CharField()
    calculation = serializers.CharField()


class StepFieldPropertySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(allow_null=True)
    measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(),
        slug_field='symbol'
    )
    field_name = serializers.CharField(read_only=True)

    class Meta:
        model = StepFieldProperty
        fields = ('id', 'measure', 'amount', 'label',
                  'from_calculation', 'calculation_used', 'field_name',)


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

        instance.name = validated_data.get('label', instance.label)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        property_ids = [item['id'] for item in properties_data]
        for field in properties.all():
            if field.id not in property_ids:
                field.delete()

        for f in properties_data:
            field = StepFieldProperty(step=instance, **f)
            field.save()

        return instance


class StepFieldValueSerializer(serializers.Serializer):
    label = serializers.CharField()
    properties = StepFieldPropertyValueSerializer(many=True)


class TaskTemplateSerializer(SerializerPermissionsMixin, serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    product_input = serializers.SlugRelatedField(
        queryset=ItemType.objects.all(),
        slug_field='name'
    )
    product_input_measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(),
        slug_field='symbol'
    )
    labware = serializers.SlugRelatedField(
        queryset=ItemType.objects.all(),
        slug_field='name'
    )
    capable_equipment = serializers.SlugRelatedField(
        many=True,
        queryset=Equipment.objects.all(),
        slug_field='name'
    )
    input_files = serializers.SlugRelatedField(
        many=True,
        queryset=FileTemplate.objects.all(),
        slug_field='name'
    )
    output_files = serializers.SlugRelatedField(
        many=True,
        queryset=FileTemplate.objects.all(),
        slug_field='name'
    )
    input_fields = InputFieldTemplateSerializer(read_only=True, many=True)
    variable_fields = VariableFieldTemplateSerializer(read_only=True, many=True)
    calculation_fields = CalculationFieldTemplateSerializer(read_only=True, many=True)
    output_fields = OutputFieldTemplateSerializer(read_only=True, many=True)
    step_fields = StepFieldTemplateSerializer(read_only=True, many=True)
    store_labware_as = serializers.CharField(read_only=True)

    class Meta:
        model = TaskTemplate

    def to_representation(self, obj):
        rep = super(TaskTemplateSerializer, self).to_representation(obj)
        self.handle_calculation(rep)
        return rep

    def _replace_fields(self, match):
        """
        Replace field names with their correct values
        """
        mtch = match.group(1)
        if mtch in self.flat:
            return str(self.flat[mtch])
        return 0

    def _perform_calculation(self, calculation):
        """
        Parse and perform a calculation using a dict of fields

        Using either a dict of values to field names

        Returns a NaN if the calculation cannot be performed, e.g.
        incorrect field names.
        """
        nsp = NumericStringParser()
        field_regex = r'\{(.+?)\}'
        interpolated_calculation = re.sub(field_regex, self._replace_fields, calculation)
        try:
            result = nsp.eval(interpolated_calculation)
        except ParseException:
            return None
        return result

    def _flatten_values(self, rep):
        flat_values = {}
        for field_type in ['input_fields', 'step_fields', 'variable_fields']:
            if field_type in rep:
                for field in rep[field_type]:
                    if field_type == 'step_fields':
                        for prop in field['properties']:
                            flat_values[prop['label']] = prop['amount']
                    else:
                        flat_values[field['label']] = field['amount']
        if 'product_input_amount' in rep:
            flat_values['product_input_amount'] = rep['product_input_amount']
        return flat_values

    def handle_calculation(self, rep):
        """
        Perform calculations on all calculation fields on the task

        If any data is provided, use that as source for the calculations
        rather than the defaults on the model.
        """
        # Flatten fields into named dict/ordered dict
        # Will need some sort of defer if not completed calculation dependent on other calculation
        if 'calculation_fields' in rep:
            self.flat = self._flatten_values(rep)
            for calc in rep['calculation_fields']:
                result = self._perform_calculation(calc['calculation'])
                calc['result'] = result
        return rep


class RecalculateTaskTemplateSerializer(TaskTemplateSerializer):
    """
    Same as TaskTemplateSerializer but with ID's + no save
    """
    id = serializers.IntegerField()
    input_fields = InputFieldTemplateSerializer(many=True)
    variable_fields = VariableFieldTemplateSerializer(many=True)
    calculation_fields = CalculationFieldIDTemplateSerializer(many=True)
    output_fields = OutputFieldTemplateSerializer(many=True)
    step_fields = StepFieldTemplateSerializer(many=True)
    store_labware_as = serializers.CharField()

    def save(self):
        # NEVER allow this serializer to create a new object
        return False


class SimpleTaskTemplateSerializer(TaskTemplateSerializer):

    class Meta:
        model = TaskTemplate
        fields = ('id', 'name', 'description', 'product_input',
                  'capable_equipment', 'created_by', 'date_created',)


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
