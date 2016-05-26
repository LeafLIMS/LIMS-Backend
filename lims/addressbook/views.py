from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import list_route

from .models import Address
from .serializers import AddressSerializer

from lims.users.permissions import UserIsOwnerAccessOnly
from lims.users.filters import IsOwnerFilterBackend 

class AddressViewSet(viewsets.ModelViewSet):
    """
    Provide a list of address for the logged in user.

    **Permissions:** IsAuthenticated, UserIsOwnerAccessOnly

    **Filters:** IsOwnerFilterBackend
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated, UserIsOwnerAccessOnly]
    filter_backends = [IsOwnerFilterBackend]
