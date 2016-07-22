from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from .models import Organism


class OrganismSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organism


class ContentTypeMixin(serializers.Serializer):

    content_type_id = serializers.SerializerMethodField()

    def get_content_type_id(self, obj):
        return ContentType.objects.get_for_model(obj).id
