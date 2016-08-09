from django.contrib.auth.models import Permission

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .permissions import ExtendedObjectPermissions
from .serializers import PermissionSerializer


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (ExtendedObjectPermissions,)
