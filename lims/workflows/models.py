import re

from pint import UnitRegistry
from pyparsing import ParseException

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from jsonfield import JSONField
from model_utils.managers import InheritanceManager

from lims.projects.models import Product, Project
from lims.equipment.models import Equipment
from lims.inventory.models import ItemType, AmountMeasure
from .calculation import NumericStringParser

class Workflow(models.Model):
    name = models.CharField(max_length=50)
    order = models.CommaSeparatedIntegerField(max_length=200, blank=True)
    created_by = models.ForeignKey(User)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ('view_workflow', 'View workflow',),
        )

    def get_tasks(self):
        if self.order:
            order = [int(v) for v in self.order.split(',')]
            tasks = list(TaskTemplate.objects.filter(pk__in=order).select_subclasses())
            ordered_tasks = []
            for o in order:
                ordered_tasks.append(next((obj for obj in tasks if obj.id == o), None))
            return ordered_tasks
        return []

    def __str__(self):
        return self.name

class WorkflowProduct(models.Model):
    current_task = models.IntegerField(default=0)
    task_in_progress = models.BooleanField(default=False)
    product = models.OneToOneField(Product, related_name='on_workflow_as', unique=True)

    def __str__(self):
        return '{} at task #{}'.format(self.product.product_identifier, 
            self.current_task)

class ActiveWorkflow(models.Model):
    workflow = models.ForeignKey(Workflow)
    products = models.ManyToManyField(WorkflowProduct, blank=True, 
        related_name='activeworkflow')
    date_started = models.DateTimeField(auto_now_add=True)
    started_by = models.ForeignKey(User)

    saved = JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-date_started']
        permissions = (
            ('view_activeworkflow', 'View activeworkflow',),
        )

    def workflow_name(self):
        return self.workflow.name

    def __str__(self):
        return 'Active: {} products on {}'.format(self.products.count, self.workflow)

class DataEntry(models.Model):

    STATE = (
        ('succeded', 'Succeded'),
        ('failed', 'Failed'),
        ('repeat succeded', 'Repeat succeded'),
        ('repeat failed', 'Repeat Failed'),
    )

    product = models.ForeignKey(Product, related_name='data')
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User)
    state = models.CharField(max_length=20, choices=STATE)
    data = JSONField()

    workflow = models.ForeignKey(Workflow)
    task = models.ForeignKey('TaskTemplate')

    def __str__(self):
        return '{}: {}, {}'.format(self.date_created, self.workflow, self.task)

class TaskTemplate(models.Model):

    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    # The main input to take from the Inventory based on what
    # is attached to the Product
    product_input = models.ForeignKey(ItemType, null=True, blank=True)
    capable_equipment = models.ManyToManyField(Equipment, blank=True)

    created_by = models.ForeignKey(User)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ('view_workflowtask', 'View workflowtask',),
        )

    def _replace_fields(self, match):
        """
        Replace field names with their correct values
        """
        field = next((item for item in self.fields if item['name'] == match.group(1)), None)
        if field:
            return str(field['amount'])
        return 'NaN'

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
            return 'NaN'
        return result

    def handle_calculations(self):
        """
        Perform calculations on all calculation fields on the task

        If any data is provided, use that as source for the calculations
        rather than the defaults on the model.
        """
        calculations = filter(lambda o: o['type'] == 'calculation', self.fields)
        for calc in calculations:
            result = self._perform_calculation(calc['calculation'])
            calc['calculation_result'] = result

    def __str__(self):
        return self.name

class CalculationFieldTemplate(models.Model):
    """
    Store a calculation referenceing variables and inputs
    """
    template = models.ForeignKey(TaskTemplate, related_name='calculation_fields')
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)

    calculation = models.TextField()

    def __str__(self):
        return self.label

class InputFieldTemplate(models.Model):
    """
    An input to a task. 
    
    Can read amounts from either a calculationor an input file
    """
    template = models.ForeignKey(TaskTemplate, related_name='input_fields')
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    amount = models.FloatField()
    measure = models.ForeignKey(AmountMeasure)
    lookup_type = models.ForeignKey(ItemType)

    from_input_file = models.BooleanField(default=False)
    from_calculation = models.BooleanField(default=False)
    calculation_used = models.ForeignKey(CalculationFieldTemplate, null=True, blank=True)

    def store_value_in(self):
        return 'inventory_identifier'

    def __str__(self):
        return self.label 

class VariableFieldTemplate(models.Model):
    template = models.ForeignKey(TaskTemplate, related_name='variable_fields')
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    amount = models.FloatField()
    measure = models.ForeignKey(AmountMeasure)

    def __str__(self):
        return self.label 

class OutputFieldTemplate(models.Model):
    template = models.ForeignKey(TaskTemplate, related_name='output_fields')
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    amount = models.FloatField()
    measure = models.ForeignKey(AmountMeasure)
    lookup_type = models.ForeignKey(ItemType)

    from_calculation = models.BooleanField(default=False)
    calculation_used = models.ForeignKey(CalculationFieldTemplate, null=True, blank=True)

    def __str__(self):
        return self.label 

class StepFieldTemplate(models.Model):
    template = models.ForeignKey(TaskTemplate, related_name='step_fields')
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.label 

class StepFieldProperty(models.Model):
    step = models.ForeignKey(StepFieldTemplate, related_name='properties') 
    label = models.CharField(max_length=50)
    amount = models.FloatField()
    measure = models.ForeignKey(AmountMeasure)

    def __str__(self):
        return self.label 
