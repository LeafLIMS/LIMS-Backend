from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from .models import FileTemplate, FileTemplateField

class FileTemplateFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileTemplateField

class FileTemplateSerializer(serializers.ModelSerializer):
    fields = FileTemplateFieldSerializer(many=True) 
    class Meta:
        model = FileTemplate

    def create(self, validated_data):
        file_fields = validated_data.pop('fields')
        file_template = FileTemplate.objects.create(**validated_data)
        for field in file_fields:
            FileTemplateField.objects.create(template=file_template, **field)
        return file_template

    def update(self, instance, validated_data):
        file_fields_data = validated_data.pop('fields')
        
        file_fields = instance.fields

        instance.name = validated_data.get('name', instance.name)
        instance.save()

        field_ids = [item['id'] for item in file_fields_data]
        for field in file_fields:
            if field.id not in field_ids:
                field.delete()

        for field in file_fields_data:
            field = FileTemplateField(template=instance, **field)
            field.save()

        return instance
        
