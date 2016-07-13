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
from lims.inventory.models import Item, ItemType, AmountMeasure
from lims.filetemplate.models import FileTemplate
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
            tasks = list(TaskTemplate.objects.filter(pk__in=order))
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
    run_identifier = models.CharField(max_length=64, db_index=True)

    def product_identifier(self):
        return self.product.product_identifier

    def product_name(self):
        return self.product.name

    def product_project(self):
        return self.product.project.id

    def __str__(self):
        return '{} at task #{}'.format(self.product.product_identifier, 
            self.current_task)

class ActiveWorkflow(models.Model):
    workflow = models.ForeignKey(Workflow)
    product_statuses = models.ManyToManyField(WorkflowProduct, blank=True, 
        related_name='activeworkflow')
    date_started = models.DateTimeField(auto_now_add=True)
    started_by = models.ForeignKey(User)

    class Meta:
        ordering = ['-date_started']
        permissions = (
            ('view_activeworkflow', 'View activeworkflow',),
        )

    def workflow_name(self):
        return self.workflow.name

    def __str__(self):
        return 'Active: {} products on {}'.format(self.product_statuses.count(), self.workflow)

class DataEntry(models.Model):

    STATE = (
        ('active', 'In Progress'),
        ('succeeded', 'Succeded'),
        ('failed', 'Failed'),
        ('repeat succeeded', 'Repeat succeded'),
        ('repeat failed', 'Repeat Failed'),
    )

    run_identifier = models.CharField(max_length=64, db_index=True)

    product = models.ForeignKey(Product, related_name='data')
    item = models.ForeignKey(Item, null=True, related_name='data_entries')
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User)
    state = models.CharField(max_length=20, choices=STATE)
    data = JSONField()

    workflow = models.ForeignKey(Workflow)
    task = models.ForeignKey('TaskTemplate')

    def __str__(self):
        return '{}: {}, {}'.format(self.date_created, self.workflow, self.task)

    class Meta:
        ordering = ['-date_created']

class TaskTemplate(models.Model):

    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    # The main input to take from the Inventory based on what
    # is attached to the Product
    product_input = models.ForeignKey(ItemType, related_name='product_input')
    product_input_amount = models.IntegerField()
    product_input_measure = models.ForeignKey(AmountMeasure)

    labware = models.ForeignKey(ItemType, related_name='labware')

    capable_equipment = models.ManyToManyField(Equipment, blank=True)

    input_files = models.ManyToManyField(FileTemplate, blank=True, related_name='input_file_templates')
    output_files = models.ManyToManyField(FileTemplate, blank=True, related_name='output_file_templates')

    created_by = models.ForeignKey(User)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ('view_workflowtask', 'View workflowtask',),
        )

    def store_labware_as(self):
        return 'labware_identifier'

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
    result = models.FloatField(null=True, blank=True)

    def field_name(self):
        return self.label.lower().replace(' ', '_')

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

    def field_name(self):
        return self.label.lower().replace(' ', '_')

    def store_value_in(self):
        return 'inventory_identifier'

    def __str__(self):
        return self.label 

class VariableFieldTemplate(models.Model):
    template = models.ForeignKey(TaskTemplate, related_name='variable_fields')
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    amount = models.FloatField()
    measure = models.ForeignKey(AmountMeasure, blank=True, null=True)
    measure_not_required = models.BooleanField(default=False)

    def field_name(self):
        return self.label.lower().replace(' ', '_')

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

    def field_name(self):
        return self.label.lower().replace(' ', '_')

    def __str__(self):
        return self.label 

class StepFieldTemplate(models.Model):
    template = models.ForeignKey(TaskTemplate, related_name='step_fields')
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)

    def field_name(self):
        return self.label.lower().replace(' ', '_')

    def __str__(self):
        return self.label 

class StepFieldProperty(models.Model):
    step = models.ForeignKey(StepFieldTemplate, related_name='properties') 
    label = models.CharField(max_length=50)
    amount = models.FloatField()
    measure = models.ForeignKey(AmountMeasure)

    from_calculation = models.BooleanField(default=False)
    calculation_used = models.ForeignKey(CalculationFieldTemplate, null=True, blank=True)

    def field_name(self):
        return self.label.lower().replace(' ', '_')

    def __str__(self):
        return self.label 
