from django.contrib.auth.models import User

from rest_framework import serializers

from lims.inventory.models import ItemType
from lims.inventory.serializers import LinkedItemSerializer
from lims.crm.serializers import CRMProjectSerializer
from lims.permissions.permissions import (SerializerPermissionsMixin,
                                          SerializerReadOnlyPermissionsMixin)
from lims.shared.models import Organism
from .models import (Project, ProjectStatus, Product, ProductStatus, Comment, WorkLog)
from lims.datastore.serializers import CompactDataEntrySerializer, AttachmentSerializer
from .parsers import DesignFileParser
from lims.inventory.models import Item


class ProjectSerializer(SerializerPermissionsMixin, serializers.ModelSerializer):
    project_identifier = serializers.CharField(read_only=True)
    identifier = serializers.IntegerField(read_only=True)
    primary_lab_contact = serializers.SlugRelatedField(
        queryset=User.objects.all(),
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
        fields = '__all__'
        read_only_fields = ('date_started',)


class SimpleProductSerializer(SerializerReadOnlyPermissionsMixin, serializers.ModelSerializer):
    product_identifier = serializers.CharField(read_only=True)
    runs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    on_run = serializers.BooleanField(read_only=True)
    product_type = serializers.SlugRelatedField(
        queryset=ItemType.objects.all(),
        slug_field='name',
    )
    linked_inventory = LinkedItemSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['product_identifier', 'runs', 'on_run', 'product_type', 'name',
                  'linked_inventory']


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
        fields = '__all__'


class DetailedProductSerializer(ProductSerializer):
    linked_inventory = LinkedItemSerializer(many=True, read_only=True)
    data = CompactDataEntrySerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(read_only=True, many=True)
    sbol_diagram = serializers.SerializerMethodField()
    has_design_file = serializers.SerializerMethodField()

    def get_sbol_diagram(self, obj):
        if obj.sbol:
            parser = DesignFileParser(obj.sbol)
            elements = parser.sbol_to_list()
            for e in elements:
                for sub in e:
                    try:
                        item = Item.objects.get(name=sub['name'])
                    except Item.DoesNotExist:
                        pass
                    else:
                        sub['item'] = item.id
            return elements
        return []

    def get_has_design_file(self, obj):
        if obj.design:
            return True
        return False


class ProductStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductStatus
        fields = '__all__'


class ProjectStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectStatus
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = '__all__'


class WorkLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkLog
        fields = '__all__'
