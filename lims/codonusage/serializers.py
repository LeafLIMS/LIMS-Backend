from rest_framework import serializers

from .models import CodonUsageTable, CodonUsage


class CodonUsageTableSerializer(serializers.ModelSerializer):
    species = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = CodonUsageTable


class CodonUsageSerializer(serializers.ModelSerializer):

    class Meta:
        model = CodonUsage
        exclude = ('table',)
