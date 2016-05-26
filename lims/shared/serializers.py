from rest_framework import serializers

from .models import Organism

class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism
