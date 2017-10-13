
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

import django_filters

from lims.permissions.permissions import IsInStaffGroupOrRO
from lims.shared.mixins import AuditTrailViewMixin

from lims.shared.mixins import StatsViewMixin
from .models import Equipment, EquipmentReservation
from .serializers import EquipmentSerializer, EquipmentReservationSerializer


class EquipmentViewSet(AuditTrailViewMixin, viewsets.ModelViewSet, StatsViewMixin):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filter_fields = ('can_reserve', 'status',)
    search_fields = ('name',)
    permission_classes = (IsInStaffGroupOrRO,)


class EquipmentReservationFilter(django_filters.FilterSet):
    start = django_filters.IsoDateTimeFilter()
    start__gte = django_filters.IsoDateTimeFilter(name='start', lookup_expr='gte')
    start__lte = django_filters.IsoDateTimeFilter(name='start', lookup_expr='lte')
    end = django_filters.IsoDateTimeFilter()
    end__lte = django_filters.IsoDateTimeFilter(name='end', lookup_expr='lte')

    class Meta:
        model = EquipmentReservation
        fields = {
            'id': ['exact'],
            'start': ['exact', 'gte', 'lte'],
            'end': ['exact', 'lte'],
            'equipment_reserved': ['exact'],
            'checked_in': ['exact'],
            'is_confirmed': ['exact'],
            'reserved_by__username': ['exact'],
        }


class EquipmentReservationViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = EquipmentReservation.objects.all()
    serializer_class = EquipmentReservationSerializer
    filter_class = EquipmentReservationFilter

    def perform_create(self, serializer):
        if self.request.user.groups.filter(name='staff').exists():
            serializer.validated_data['is_confirmed'] = True
            serializer.validated_data['confirmed_by'] = self.request.user
        serializer.save(reserved_by=self.request.user)

    def perform_update(self, serializer):
        if (serializer.instance.reserved_by == self.request.user or
                self.request.user.groups.filter(name='staff').exists()):
            serializer.save()
        else:
            raise PermissionDenied()

    def destroy(self, request, pk=None):
        if (request.user == self.get_object().reserved_by or
                request.user.groups.filter(name='staff').exists()):
            return super(EquipmentReservationViewSet, self).destroy(request, self.get_object().id)
        else:
            return Response({'message': 'You must have permission to delete'}, status=403)
