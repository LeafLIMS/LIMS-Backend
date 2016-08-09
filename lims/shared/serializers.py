from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from .models import Organism


class OrganismSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organism
