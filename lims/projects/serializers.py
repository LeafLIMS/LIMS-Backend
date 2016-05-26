from django.contrib.auth.models import User

from rest_framework import serializers

from lims.inventory.models import ItemType
from lims.inventory.serializers import SimpleGenericItemSerializer
from lims.workflows.serializers import DataEntrySerializer
from .models import (Project, Product, Comment, WorkLog) 

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
    product_identifier = serializers.CharField(read_only=True)
    on_workflow_as = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = Product

class DetailedProductSerializer(ProductSerializer):
    data = DataEntrySerializer(many=True, read_only=True)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment

class WorkLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLog
