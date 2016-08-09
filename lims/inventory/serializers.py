from rest_framework import serializers

from lims.permissions.permissions import SerializerPermissionsMixin
from .models import (Set, Item, ItemProperty, ItemTransfer,
                     ItemType,
                     AmountMeasure, Location)


class SetSerializer(SerializerPermissionsMixin, serializers.ModelSerializer):
    number_of_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Set


class ItemTypeSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(
        queryset=ItemType.objects.all(),
        slug_field='name',
        required=False,
        allow_null=True
    )
    has_children = serializers.BooleanField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    root = serializers.CharField(read_only=True)

    class Meta:
        model = ItemType
        fields = ('id', 'name', 'display_name', 'parent', 'level', 'has_children', 'root')


class LocationSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(
        queryset=Location.objects.all(),
        slug_field='code',
        required=False,
        allow_null=True
    )
    has_children = serializers.BooleanField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    code = serializers.CharField(required=True)

    class Meta:
        model = Location
        fields = ('id', 'name', 'code', 'display_name', 'parent', 'level', 'has_children',)


class ItemPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = ItemProperty


class ItemTransferSerializer(serializers.ModelSerializer):
    amount_measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(),
        slug_field='symbol'
    )

    class Meta:
        model = ItemTransfer


class ItemTransferPreviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = ItemTransfer
        depth = 2


class ItemSerializer(serializers.ModelSerializer, SerializerPermissionsMixin):
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    added_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    amount_measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(), slug_field='symbol')
    item_type = serializers.SlugRelatedField(queryset=ItemType.objects.all(), slug_field='name')
    location = serializers.SlugRelatedField(queryset=Location.objects.all(), slug_field='code')
    location_path = serializers.CharField(read_only=True)

    sets = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = Item
        read_only_fields = ('transfers', 'created_from',)


class LinkedItemSerializer(serializers.ModelSerializer):
    item_type = serializers.SlugRelatedField(queryset=ItemType.objects.all(), slug_field='name')

    class Meta:
        model = Item
        fields = ('id', 'name', 'identifier', 'item_type',)


class DetailedItemSerializer(ItemSerializer):
    transfers = ItemTransferSerializer(many=True, read_only=True)
    properties = ItemPropertySerializer(many=True, read_only=True)
    created_from = LinkedItemSerializer(many=True, read_only=True)


class SimpleItemSerializer(serializers.ModelSerializer):
    amount_measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(), slug_field='symbol')

    class Meta:
        model = Item
        fields = ('name', 'identifier',
                  'amount_measure', 'amount_available')


class AmountMeasureSerializer(serializers.ModelSerializer):

    class Meta:
        model = AmountMeasure


class ItemTransferSerializer(serializers.ModelSerializer):

    class Meta:
        model = ItemTransfer
