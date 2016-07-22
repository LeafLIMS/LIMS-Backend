
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from lims.permissions.permissions import IsInAdminGroupOrRO

from .models import CodonUsageTable, CodonUsage
from .serializers import CodonUsageTableSerializer, CodonUsageSerializer


class CodonUsageTableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CodonUsageTable.objects.all()
    serializer_class = CodonUsageTableSerializer
    permission_classes = (IsInAdminGroupOrRO,)

    @detail_route()
    def codons(self, request, pk=None):
        codons = CodonUsage.objects.filter(table=self.get_object())
        serializer = CodonUsageSerializer(codons, many=True)
        return Response(serializer.data)
