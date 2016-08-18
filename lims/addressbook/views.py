from rest_framework import viewsets
from rest_framework.serializers import ValidationError

from .models import Address
from .serializers import AddressSerializer

from lims.permissions.permissions import IsAddressOwner, IsAddressOwnerFilter


class AddressViewSet(viewsets.ModelViewSet):
    """
    Provide a list of address for the logged in user.

    **Permissions:** IsAuthenticated, UserIsOwnerAccessOnly

    **Filters:** IsOwnerFilterBackend
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = (IsAddressOwner,)
    filter_backends = (IsAddressOwnerFilter,)

    def perform_create(self, serializer):
        # Allow an admin user to set the user
        # for instance is adding a new address
        if self.request.user.groups.filter(name='admin').exists():
            serializer.save()
        else:
            # No. You are not admin, you cannot add user.
            if self.request.user != serializer.validated_data['user']:
                raise ValidationError('You cannot add an address to another user')
            serializer.save(user=self.request.user)
