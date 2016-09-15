from rest_framework import serializers

from .models import DataFile, DataEntry


class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile


class DataEntrySerializer(serializers.ModelSerializer):
    """
    workflow = serializers.SlugRelatedField(
        queryset=Workflow.objects.all(),
        slug_field='name'
    )
    task = serializers.SlugRelatedField(
        queryset=TaskTemplate.objects.all(),
        slug_field='name'
    )
    item = serializers.SlugRelatedField(
        queryset=Item.objects.all(),
        slug_field='name'
    )
    """
    product_name = serializers.CharField()

    class Meta:
        model = DataEntry
