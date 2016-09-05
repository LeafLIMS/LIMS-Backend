from rest_framework import serializers

from .models import CopyFileDriver


class CopyFileDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = CopyFileDriver
