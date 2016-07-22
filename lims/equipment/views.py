
from rest_framework import viewsets
from rest_framework.response import Response

import django_filters

from lims.permissions.permissions import IsInAdminGroupOrRO

from .models import Equipment, EquipmentReservation
from .serializers import EquipmentSerializer, EquipmentReservationSerializer


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filter_fields = ('can_reserve',)
    search_fields = ('name',)
    permission_classes = (IsInAdminGroupOrRO,)


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

    def perform_create(self, serializer):
        serializer.save(reserved_by=self.request.user)

    def perform_update(self, serializer):
        if serializer.reserved_by == self.request.user or self.request.user.is_staff:
            serializer.save()

    def destroy(self, request, pk=None):
        if request.user == self.get_object().reserved_by or request.user.is_staff:
            return super(EquipmentReservationViewSet, self).destroy(request, self.get_object().id)
        else:
            return Response({'message': 'You must have permission to delete'}, status=403)
