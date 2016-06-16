from django.contrib.auth.models import User

from rest_framework import serializers

from lims.inventory.models import ItemType
from lims.inventory.serializers import SimpleItemSerializer, LinkedItemSerializer
from lims.shared.models import Organism
from .models import (Project, Product, ProductStatus, Comment, WorkLog) 

class ProjectSerializer(serializers.ModelSerializer):
    project_identifier = serializers.CharField(read_only=True)
    primary_lab_contact = serializers.SlugRelatedField(
            queryset = User.objects.filter(is_staff=True),
            slug_field = 'username',
        )
    class Meta:
        model = Project
        read_only_fields = ('date_started',)

class ProductSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(read_only=True)
    product_identifier = serializers.CharField(read_only=True)
    #on_workflow_as = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    on_workflow_as = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.SlugRelatedField(
            queryset = User.objects.filter(is_staff=True),
            slug_field = 'username',
        )
    product_type = serializers.SlugRelatedField(
            queryset = ItemType.objects.all(),
            slug_field = 'name',
        )
    status = serializers.SlugRelatedField(
            queryset = ProductStatus.objects.all(),
            slug_field = 'name',
        )
    optimised_for = serializers.SlugRelatedField(
            required = False,
            allow_null = True,
            queryset = Organism.objects.all(),
            slug_field = 'name',
        )
    '''
    linked_inventory_details = LinkedItemSerializer(read_only=True,
            many=True,
            source='linked_inventory'
            )
    '''

    class Meta:
        model = Product

class ProductStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStatus

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment

class WorkLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLog
