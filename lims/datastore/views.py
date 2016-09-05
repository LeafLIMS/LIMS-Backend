from rest_framework import viewsets

from .models import DataFile
from .serializers import DataFileSerializer


class DataFileViewSet(viewsets.ModelViewSet):
    queryset = DataFile.objects.all()
    serializer_class = DataFileSerializer
