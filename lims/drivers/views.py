from rest_framework import viewsets

from .models import CopyFileDriver
from .serializers import CopyFileDriverSerializer


class CopyFileDriverViewSet(viewsets.ModelViewSet):
    queryset = CopyFileDriver.objects.all()
    serializer_class = CopyFileDriverSerializer
