from django.contrib.auth.models import User

from rest_framework import serializers

from .models import DataFile, DataEntry, Attachment


class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile
        fields = '__all__'


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
        fields = '__all__'


class CompactDataEntrySerializer(DataEntrySerializer):

    class Meta:
        fields = ('id', 'task_run_identifier', 'date_created', 'state',
                  'run', 'created_by', 'task',)
        model = DataEntry


class AttachmentSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username'
    )
    attachment_name = serializers.CharField(read_only=True)

    class Meta:
        model = Attachment
        fields = '__all__'
