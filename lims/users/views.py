from django.contrib.auth.models import User, Group

from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import list_route

import django_filters

from lims.addressbook.serializers import AddressSerializer
from lims.crm.helpers import CRMCreateContact
from lims.crm.serializers import CreateCRMAccountSerializer
from .serializers import (UserSerializer, StaffUserSerializer, SuperUserSerializer,
                          GroupSerializer, RegisterUserSerializer)
from lims.permissions.permissions import (IsInAdminGroupOrRO, IsInAdminGroupOrTheUser)
from lims.shared.mixins import AuditTrailViewMixin


class ObtainAuthToken(APIView):
    """
    Customisation of ObtainAuthToken class to return an organisation along with
    the token.
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            usr = User.objects.get(username=user)

            groups = [g.name for g in user.groups.all()]

            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key,
                             'id': usr.id, 'groups': groups})
        return Response({'message': 'Username/password incorrect'}, status=400)


class UserFilter(django_filters.FilterSet):
    has_crm_details = django_filters.MethodFilter()

    def filter_has_crm_details(self, queryset, value):
        if value == 'False':
            return queryset.filter(crmaccount__isnull=True)
        elif value == 'True':
            return queryset.filter(crmaccount__isnull=False)
        return queryset

    class Meta:
        model = User
        fields = ['has_crm_details']


class UserViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    """
    User data.

    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsInAdminGroupOrTheUser,)
    filter_class = UserFilter

    def get_queryset(self):
        if self.request.user.groups.filter(name='staff').exists():
            return User.objects.all()
        else:
            return User.objects.filter(username=self.request.user.username)

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return SuperUserSerializer
        elif self.request.user.is_staff:
            return StaffUserSerializer
        return UserSerializer

    @list_route()
    def staff(self, request):
        results = self.get_queryset().filter(groups__name='staff')
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a user in the system. Access to all without authentication.

        Checks/creates a CRM account and address if possible.
        """
        required_data = RegisterUserSerializer(data=request.data)
        serializer = UserSerializer(data=request.data)
        if required_data.is_valid():
            # It's already been validated above but we still need
            # to re-validate for the serializer to work
            serializer.is_valid()
            instance = serializer.save()
            # Create and address and link to CRM
            request.data['user'] = instance.username
            address = AddressSerializer(data=request.data)
            if address.is_valid():
                address.save()
            # Validate data for CRM
            crm_data = CreateCRMAccountSerializer(data=request.data)
            crm_data.is_valid()
            CRMCreateContact(request, crm_data.validated_data)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsInAdminGroupOrRO,)
