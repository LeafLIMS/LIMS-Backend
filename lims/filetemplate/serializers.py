
from rest_framework import serializers

from .models import FileTemplate, FileTemplateField


class FileTemplateFieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileTemplateField
        fields = ('id', 'name', 'required', 'map_to', 'is_identifier', 'is_property',)
        # This is required for it to show up in the nested
        # FileTemplateSerializer. Should never be a problem
        # as you can't access this through an API endpoint
        extra_kwargs = {"id": {"required": False, "read_only": False}}


class FileTemplateSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(read_only=True)
    fields = FileTemplateFieldSerializer(many=True)

    class Meta:
        model = FileTemplate

    def create(self, validated_data):
        file_fields = validated_data.pop('fields')
        file_template = FileTemplate.objects.create(**validated_data)
        for field in file_fields:
            # Just in case lets make sure an ID isn't sent along
            if 'id' in field:
                field.pop('id')
            FileTemplateField.objects.create(template=file_template, **field)
        return file_template

    def update(self, instance, validated_data):
        file_fields_data = validated_data.pop('fields')

        file_fields = instance.fields

        instance.name = validated_data.get('name', instance.name)
        instance.save()

        field_ids = [item['id'] for item in file_fields_data if 'id' in item]
        for field in file_fields.all():
            if field.id not in field_ids:
                field.delete()

        for f in file_fields_data:
            try:
                field = FileTemplateField.objects.get(pk=f['id'])
                f.pop('id')
                for (key, value) in f.items():
                    setattr(field, key, value)
            except (FileTemplateField.DoesNotExist, KeyError):
                if 'id' in f:
                    f.pop('id')
                field = FileTemplateField(template=instance, **f)
            field.save()

        return instance
