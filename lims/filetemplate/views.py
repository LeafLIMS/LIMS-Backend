
from rest_framework import viewsets

from .models import FileTemplate, FileTemplateField
from .serializers import FileTemplateSerializer, FileTemplateFieldSerializer


class FileTemplateViewSet(viewsets.ModelViewSet):
    queryset = FileTemplate.objects.all()
    serializer_class = FileTemplateSerializer


class FileTemplateFieldSerializer(viewsets.ModelViewSet):
    queryset = FileTemplateField.objects.all()
    serializer_class = FileTemplateFieldSerializer
