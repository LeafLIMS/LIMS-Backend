
from rest_framework import viewsets

from lims.permissions.permissions import IsInAdminGroupOrRO

from .models import FileTemplate
from .serializers import FileTemplateSerializer


class FileTemplateViewSet(viewsets.ModelViewSet):
    queryset = FileTemplate.objects.all()
    serializer_class = FileTemplateSerializer
    permission_classes = (IsInAdminGroupOrRO,)
