from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from rest_framework import serializers

from lims.shared.models import Organism
from lims.shared.serializers import OrganismSerializer
from .models import (Set, PartType, Part, Enzyme, Primer,
                        ItemType, Consumable, GenericItem,
                        AmountMeasure, Location, AmountMeasure)

class SetSerializer(serializers.ModelSerializer):
    number_of_items = serializers.IntegerField(read_only=True)
    class Meta:
        model = Set

class PartTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartType
        depth = 1

class ItemTypeSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(
            queryset=ItemType.objects.all(),
            slug_field='name',
            required=False
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
            required=False
            )
    has_children = serializers.BooleanField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    code = serializers.CharField(required=True)
    class Meta:
        model = Location
        fields = ('id', 'name', 'code', 'display_name', 'parent', 'level', 'has_children',)

class GenericItemSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name') 
    added_by = serializers.SlugRelatedField(queryset=User.objects.filter(is_staff=True), slug_field='username')
    amount_measure = serializers.SlugRelatedField(queryset=AmountMeasure.objects.all(), slug_field='symbol')
    item_type = serializers.SlugRelatedField(queryset=ItemType.objects.all(), slug_field='name')
    of_type = serializers.CharField(read_only=True)
    location = serializers.SlugRelatedField(queryset=Location.objects.all(), slug_field='code')
    location_path = serializers.CharField(read_only=True)

    sets = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = GenericItem

class SimpleGenericItemSerializer(serializers.ModelSerializer):
    amount_measure = serializers.SlugRelatedField(queryset=AmountMeasure.objects.all(), slug_field='symbol')

    class Meta:
        model = GenericItem
        fields = ('name', 'identifier', 
                'amount_measure', 'amount_available')

class PartSerializer(GenericItemSerializer):
    originating_organism = serializers.SlugRelatedField(queryset=Organism.objects.all(), slug_field='name')
    optimised_for_organism = serializers.SlugRelatedField(queryset=Organism.objects.all(), slug_field='name', 
            required=False, allow_null=True)

    class Meta:
        model = Part

class EnzymeSerializer(GenericItemSerializer):
    class Meta:
        model = Enzyme

class PrimerSerializer(GenericItemSerializer):
    class Meta:
        model = Primer

class ConsumableSerializer(GenericItemSerializer):
    class Meta:
        model = Consumable

class AmountMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmountMeasure
