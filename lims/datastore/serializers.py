from rest_framework import serializers

from .models import DataFile, DataEntry


class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile


class DataEntrySerializer(serializers.ModelSerializer):
    run = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    created_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    product_name = serializers.CharField()

    class Meta:
        model = DataEntry


class CompactDataEntrySerializer(DataEntrySerializer):

    class Meta:
        fields = ('id', 'task_run_identifier', 'date_created', 'state',
                  'run', 'created_by', 'task',)
        model = DataEntry
