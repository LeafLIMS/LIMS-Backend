from rest_framework import viewsets

from .models import Organism
from .serializers import OrganismSerializer


class OrganismViewSet(viewsets.ModelViewSet):
    queryset = Organism.objects.all()
    serializer_class = OrganismSerializer
    search_fields = ('name', 'common_name',)
