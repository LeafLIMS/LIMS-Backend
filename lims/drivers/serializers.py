from rest_framework import serializers

from .models import CopyFileDriver, CopyFilePath


class CopyFilePathSerializer(serializers.ModelSerializer):
    class Meta:
        model = CopyFilePath
        extra_kwargs = {"id": {"required": False, "read_only": False}}


class CopyFileDriverSerializer(serializers.ModelSerializer):
    locations = CopyFilePathSerializer(many=True)

    class Meta:
        model = CopyFileDriver

    def create(self, validated_data):
        file_paths = validated_data.pop('locations')
        file_driver = CopyFileDriver.objects.create(**validated_data)
        for path in file_paths:
            # Just in case lets make sure an ID isn't sent along
            if 'id' in path:
                path.pop('id')
            CopyFilePath.objects.create(driver=file_driver, **path)
        return file_driver

    def update(self, instance, validated_data):
        file_paths_data = validated_data.pop('locations')

        file_paths = instance.locations

        instance = CopyFileDriver(id=instance.id, **validated_data)
        instance.save()

        path_ids = [item['id'] for item in file_paths_data if 'id' in item]
        for path in file_paths.all():
            if path.id not in path_ids:
                path.delete()

        for f in file_paths_data:
            try:
                path = CopyFilePath.objects.get(pk=f['id'])
                f.pop('id')
                for (key, value) in f.items():
                    setattr(path, key, value)
            except (CopyFilePath.DoesNotExist, KeyError):
                if 'id' in f:
                    f.pop('id')
                path = CopyFilePath(driver=instance, **f)
            path.save()
        return instance
