from rest_framework import serializers

from lims.permissions.permissions import SerializerPermissionsMixin
from .models import (Set, Item, ItemProperty, ItemTransfer,
                     ItemType,
                     AmountMeasure, Location)


class SetSerializer(serializers.ModelSerializer, SerializerPermissionsMixin):
    number_of_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Set
        fields = '__all__'


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
    parent_name = serializers.CharField(read_only=True, source='parent.name')
    code = serializers.CharField(required=True)

    class Meta:
        model = Location
        fields = ('id', 'name', 'code', 'display_name', 'parent',
                  'parent_name', 'level', 'has_children',)


class ItemPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = ItemProperty
        fields = ('id', 'name', 'value',)


class ItemTransferSerializer(serializers.ModelSerializer):
    amount_measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(),
        slug_field='symbol'
    )
    # Whut???
    item_name = serializers.CharField(read_only=True)

    class Meta:
        model = ItemTransfer
        fields = '__all__'


class ItemPreviewSerializer(serializers.ModelSerializer):
    """
    Provided a limited set of fields for preview purposes
    """
    class Meta:
        model = Item
        depth = 1
        fields = ('id', 'name', 'identifier', 'in_inventory', 'amount_available',
                  'item_type', 'amount_measure', 'concentration', 'concentration_measure',
                  'location', 'location_path',)


class ItemTransferPreviewSerializer(serializers.ModelSerializer):
    """
    Provide a limited set of fields for previewing ItemTransfers
    """
    item = ItemPreviewSerializer()
    is_valid = serializers.BooleanField(read_only=True, required=False, default=True)

    class Meta:
        model = ItemTransfer
        depth = 1
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer, SerializerPermissionsMixin):
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    added_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    amount_measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(), slug_field='symbol')
    concentration_measure = serializers.SlugRelatedField(
        required=False, allow_null=True,
        queryset=AmountMeasure.objects.all(), slug_field='symbol')
    item_type = serializers.SlugRelatedField(queryset=ItemType.objects.all(), slug_field='name')
    location = serializers.SlugRelatedField(queryset=Location.objects.all(), slug_field='code')
    location_path = serializers.CharField(read_only=True)

    sets = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = Item
        read_only_fields = ('transfers', 'created_from',)
        fields = '__all__'


class LinkedItemSerializer(serializers.ModelSerializer):
    item_type = serializers.SlugRelatedField(queryset=ItemType.objects.all(), slug_field='name')

    class Meta:
        model = Item
        fields = ('id', 'name', 'identifier', 'item_type',)


class DetailedItemSerializer(ItemSerializer):
    transfers = ItemTransferSerializer(many=True, read_only=True)
    properties = ItemPropertySerializer(many=True)
    created_from = LinkedItemSerializer(many=True, read_only=True)

    def create(self, validated_data):
        property_fields = validated_data.pop('properties')
        item = Item.objects.create(**validated_data)
        for field in property_fields:
            # Just in case lets make sure an ID isn't sent along
            if 'id' in field:
                field.pop('id')
            ItemProperty.objects.create(item=item, **field)
        return item

    def update(self, instance, validated_data):
        property_fields_data = validated_data.pop('properties')

        property_fields = instance.properties

        for (key, value) in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        property_ids = [item['name'] for item in property_fields_data]
        for field in property_fields.all():
            if field.name not in property_ids:
                field.delete()

        for f in property_fields_data:
            try:
                field = ItemProperty.objects.get(name=f['name'], item=instance)
                field.value = f['value']
            except ItemProperty.DoesNotExist:
                field = ItemProperty(item=instance, **f)
            field.save()

        return instance


class SimpleItemSerializer(serializers.ModelSerializer):
    amount_measure = serializers.SlugRelatedField(
        queryset=AmountMeasure.objects.all(), slug_field='symbol')
    concentration_measure = serializers.SlugRelatedField(
        required=False, allow_null=True,
        queryset=AmountMeasure.objects.all(), slug_field='symbol')

    class Meta:
        model = Item
        fields = ('name', 'identifier',
                  'amount_measure', 'amount_available',
                  'concentration', 'concentration_measure')


class AmountMeasureSerializer(serializers.ModelSerializer):

    class Meta:
        model = AmountMeasure
        fields = '__all__'
