from django.contrib.auth.models import User

from rest_framework import serializers

from .models import (Workflow, ActiveWorkflow, DataEntry, TaskTemplate, 
    WorkflowSample)
from lims.workflows.serializers import WorkflowSerializer
from lims.projects.serializers import DetailedSampleSerializer, SampleSerializer

class WorkflowSampleSerializer(serializers.ModelSerializer):
    sample = SampleSerializer(read_only=True) 
    class Meta:
        model = WorkflowSample

class ActiveWorkflowSerializer(serializers.ModelSerializer):
    workflow_data = WorkflowSerializer(read_only=True, source='workflow')
    started_by = serializers.SlugRelatedField(
        queryset = User.objects.all(),
        slug_field = 'username'
    )
    class Meta:
        model = ActiveWorkflow

class DetailedActiveWorkflowSerializer(serializers.ModelSerializer):
    samples = WorkflowSampleSerializer(read_only=True, many=True)
    workflow_name = serializers.CharField(read_only=True)
    class Meta:
        model = ActiveWorkflow
