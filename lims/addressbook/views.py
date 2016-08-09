
from rest_framework import viewsets

from .models import Address
from .serializers import AddressSerializer

from lims.users.filters import IsOwnerFilterBackend


class AddressViewSet(viewsets.ModelViewSet):
    """
    Provide a list of address for the logged in user.

    **Permissions:** IsAuthenticated, UserIsOwnerAccessOnly

    **Filters:** IsOwnerFilterBackend
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    filter_backends = [IsOwnerFilterBackend]

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
        serializer.save(user=self.request.user)
