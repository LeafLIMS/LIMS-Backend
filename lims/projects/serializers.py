from django.contrib.auth.models import User

from rest_framework import serializers

from lims.inventory.models import ItemType
from lims.inventory.serializers import LinkedItemSerializer
from lims.crm.serializers import CRMProjectSerializer
from lims.permissions.permissions import (SerializerPermissionsMixin,
                                          SerializerReadOnlyPermissionsMixin)
from lims.shared.models import Organism
from .models import (Project, Product, ProductStatus, Comment, WorkLog)
from lims.datastore.serializers import CompactDataEntrySerializer, AttachmentSerializer


class ProjectSerializer(SerializerPermissionsMixin, serializers.ModelSerializer):
    project_identifier = serializers.CharField(read_only=True)
    identifier = serializers.IntegerField(read_only=True)
    primary_lab_contact = serializers.SlugRelatedField(
        queryset=User.objects.filter(groups__name='staff'),
        slug_field='username',
    )
    created_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
    )
    crm_project = CRMProjectSerializer(read_only=True)
    links = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Project
        read_only_fields = ('date_started',)


class ProductSerializer(SerializerReadOnlyPermissionsMixin, serializers.ModelSerializer):
    identifier = serializers.CharField(read_only=True)
    product_identifier = serializers.CharField(read_only=True)
    runs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    on_run = serializers.BooleanField(read_only=True)
    created_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
    )
    product_type = serializers.SlugRelatedField(
        queryset=ItemType.objects.all(),
        slug_field='name',
    )
    status = serializers.SlugRelatedField(
        queryset=ProductStatus.objects.all(),
        slug_field='name',
    )
    optimised_for = serializers.SlugRelatedField(
        required=False,
        allow_null=True,
        queryset=Organism.objects.all(),
        slug_field='name',
    )
    design = serializers.CharField(allow_blank=True,
                                   required=False,
                                   write_only=True)

    class Meta:
        model = Product


class DetailedProductSerializer(ProductSerializer):
    linked_inventory = LinkedItemSerializer(many=True, read_only=True)
    data = CompactDataEntrySerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(read_only=True, many=True)


class ProductStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductStatus


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment


class WorkLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkLog
