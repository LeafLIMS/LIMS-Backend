
from rest_framework import viewsets
from rest_framework.response import Response

import django_filters

from .models import Equipment, EquipmentReservation
from .serializers import EquipmentSerializer, EquipmentReservationSerializer


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filter_fields = ('can_reserve',)
    search_fields = ('name',)


class EquipmentReservationFilter(django_filters.FilterSet):

    class Meta:
        model = EquipmentReservation
        fields = {
            'id': ['exact'],
            'start': ['exact', 'gte'],
            'end': ['exact', 'lte'],
            'equipment_reserved': ['exact'],
        }


class EquipmentReservationViewSet(viewsets.ModelViewSet):
    queryset = EquipmentReservation.objects.all()
    serializer_class = EquipmentReservationSerializer
    filter_class = EquipmentReservationFilter

    def destroy(self, request, pk=None):
        if request.user == self.get_object().reserved_by or request.user.is_staff:
            return super(EquipmentReservationViewSet, self).destroy(request, self.get_object().id)
        else:
            return Response({'message': 'You must have permission to delete'}, status=403)
