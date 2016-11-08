from rest_framework import viewsets

from lims.permissions.permissions import IsInAdminGroupOrRO
from lims.shared.mixins import AuditTrailViewMixin

from .models import Organism
from .serializers import OrganismSerializer


class OrganismViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = Organism.objects.all()
    serializer_class = OrganismSerializer
    search_fields = ('name', 'common_name',)
    permission_classes = (IsInAdminGroupOrRO,)
