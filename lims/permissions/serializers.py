from django.contrib.auth.models import Permission

from rest_framework import serializers


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serialize Permission model
    """
    class Meta:
        model = Permission
        fields = '__all__'
