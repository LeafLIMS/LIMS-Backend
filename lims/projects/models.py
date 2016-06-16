from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from jsonfield import JSONField

from gm2m import GM2MField

from lims.shared.models import Organism
from lims.inventory.models import ItemType, Item
from lims.inventory.helpers import serialized_item_lookup
from lims.orders.models import Order

class Project(models.Model):
    """
    A project is a container for products and contains key identifiying information
    """
    def create_identifier():
        """
        Create an identifier for the project based on the last ID, starting from given value
        """
        last = Project.objects.order_by('-identifier')
        if last.count() > 0:
            return last[0].identifier + 1
        return settings.PROJECT_IDENTIFIER_START

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    identifier = models.IntegerField(default=create_identifier)
    order = models.ForeignKey(Order, related_name='associated_projects', blank=True, null=True)
    date_started = models.DateTimeField(auto_now_add=True)
    archive = models.BooleanField(default=False)

    project_identifier = models.CharField(default='', max_length=20)

    primary_lab_contact = models.ForeignKey(User, limit_choices_to={'is_staff': True})

    class Meta:
        permissions = (
            ('view_project', 'View project',),
        )

    def create_project_identifier(self):
        """
        Return the project identifier with a prefix
        """
        return '{}{}'.format(settings.PROJECT_IDENTIFIER_PREFIX, self.identifier)

    def save(self, force_insert=False, force_update=False, **kwargs):
        self.project_identifier = self.create_project_identifier()
        super(Project, self).save(force_insert, force_update, **kwargs)

    def __str__(self):
        return self.name

class ProductStatus(models.Model):
    """
    The status of a product as it moves through workflows
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    A representation of a product as it progresses through the system
    """

    identifier = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    status = models.ForeignKey(ProductStatus) 
    flag_issue = models.BooleanField(default=False)
    product_type = models.ForeignKey(ItemType)
    optimised_for = models.ForeignKey(Organism, blank=True, null=True)

    # TODO: Ability to add "design" from CAD tool to Product

    # A project prefixed (e.g. GM1-1) version of the identifier
    product_identifier = models.CharField(default='', max_length=20, db_index=True)

    created_by = models.ForeignKey(User, limit_choices_to={'is_staff': True}, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified_on = models.DateTimeField(auto_now=True)

    project = models.ForeignKey(Project)

    # One design per product as it should only be making (ultimately) one thing
    design = models.FileField(blank=True, null=True)

    # Anything created or linked in the inventroy to this product
    linked_inventory = models.ManyToManyField(Item, blank=True, 
            related_name='products')

    class Meta:
        permissions = (
            ('view_product', 'View product',),
        )

    def create_product_identifier(self):
        """
        Create a prefixed version of the identifier based on the project 
        it is part of
        """
        return '{}-{}'.format(self.project.project_identifier, self.identifier)

    def save(self, force_insert=False, force_update=False, **kwargs):
        if self.identifier == 0:
            try:
                last = Product.objects.filter(project=self.project).order_by('-identifier')[0]
                self.identifier = last.identifier + 1
            except IndexError:
                self.identifier = 1
        self.product_identifier = self.create_product_identifier()
        super(Product, self).save(force_insert, force_update, **kwargs)

    def __str__(self):
        return self.name

class Comment(models.Model):
    """
    A user identifiable comment on a Product 
    """
    product = models.ForeignKey(Product)
    user = models.ForeignKey(User, limit_choices_to={'is_staff': True})
    date_created = models.DateTimeField(auto_now_add=True)
    text = models.TextField() 

    def __str__(self):
        return '{}: {}'.format(self.product, self.date_created)

class WorkLog(models.Model):
    project = models.ForeignKey(Project)
    task = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, limit_choices_to={'is_staff': True})
    start_time = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)

    def hours(self):
        diff = self.finish_time - self.start_time
        return diff//3600

    def __str__(self):
        return '{}: {} ({})'.format(self.project, self.task, self.user.username)
