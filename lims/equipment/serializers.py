
from django.contrib.auth.models import User

from psycopg2.extras import DateTimeTZRange

from rest_framework import serializers

from lims.inventory.models import Location
from .models import Equipment, EquipmentReservation


class EquipmentSerializer(serializers.ModelSerializer):
    location = serializers.SlugRelatedField(queryset=Location.objects.all(),
                                            slug_field='code')

    class Meta:
        model = Equipment


class EquipmentReservationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True)
    equipment_reserved = serializers.SlugRelatedField(
        queryset=Equipment.objects.all(),
        slug_field='name')
    confirmed_by = serializers.SlugRelatedField(
        required=False,
        queryset=User.objects.all(),
        slug_field='username')
    reserved_by = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username')

    class Meta:
        model = EquipmentReservation
        exclude = ('reservation',)

    def validate(self, data):
        if data['start'] > data['end']:
            raise serializers.ValidationError('Start date must be after end date')
        if not self.instance:
            date_range = DateTimeTZRange(data['start'], data['end'])
            overlaps = EquipmentReservation.objects.filter(
                reservation__overlap=date_range,
                equipment_reserved=data['equipment_reserved']).count()
            if overlaps > 0:
                raise serializers.ValidationError(
                    'Equipment has already been reserved during this time period')
        return data
