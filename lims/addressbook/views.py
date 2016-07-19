
from rest_framework import viewsets
from rest_framework.serializers import ValidationError
from rest_framework.permissions import IsAuthenticated

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

    def perform_create(self, serializer):
        user_id_in_new_address = serializer.validated_data["user"].id
        if user_id_in_new_address != self.request.user.id and not self.request.user.is_staff:
            raise ValidationError('Must specify your own user ID in user field of new object')
        else:
            super().perform_create(serializer)
