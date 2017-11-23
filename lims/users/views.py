from django.contrib.auth.models import User, Group
from django.conf import settings

from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import list_route, detail_route
from rest_framework.validators import ValidationError

import django_filters

from lims.addressbook.serializers import AddressSerializer
from lims.crm.helpers import CRMCreateContact
from lims.crm.serializers import CreateCRMAccountSerializer
from .serializers import (UserSerializer, GroupSerializer,
                          RegisterUserSerializer, SimpleUserSerializer,)
from lims.permissions.permissions import (IsInAdminGroupOrRO, IsInAdminGroupOrTheUser)
from lims.shared.mixins import AuditTrailViewMixin
from lims.users.models import ResetCode


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
                             'crm': settings.ENABLE_CRM,
                             'id': usr.id, 'groups': groups})
        return Response({'message': 'Username/password incorrect'}, status=400)


class UserFilter(django_filters.FilterSet):
    has_crm_details = django_filters.CharFilter(method='filter_has_crm_details')

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
    search_fields = ('username', 'email')
    filter_class = UserFilter

    def get_queryset(self):
        if self.request.user.groups.filter(name='admin').exists():
            # Exclude the system specific AnonymousUser from results as deleting could cause issues
            return User.objects.exclude(username='AnonymousUser')
        else:
            return User.objects.filter(username=self.request.user.username)

    @detail_route(methods=['patch'])
    def change_password(self, request, pk=None):
        """
        Reset password for a given user
        """
        new_password = request.data.get('new_password', None)
        if new_password:
            user = self.get_object()
            if request.user.id == user.id or request.user.groups.filter(name='admin').exists():
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password for {} changed'.format(user.username)})
            raise ValidationError({'message':
                                  'You do not have permissions to change this users password'})
        raise ValidationError({'message': 'You must supply a new password'})

    @list_route(methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @list_route(permission_classes=[IsAuthenticated])
    def staff(self, request):
        results = User.objects.filter(groups__name='staff')
        serializer = SimpleUserSerializer(results, many=True)
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
            if settings.ENABLE_CRM:
                crm_data = CreateCRMAccountSerializer(data=request.data)
                crm_data.is_valid()
                CRMCreateContact(request, crm_data.validated_data)
            return Response(serializer.data, status=201)
        else:
            return Response(required_data.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route(permission_classes=[AllowAny])
    def exists(self, request):
        """
        Check if a given email address exists as a user in the system
        """
        email = request.query_params.get('email', None)
        if email:
            exists = User.objects.filter(email=email).exists()
            output = {'exists': exists}
            if exists:
                user = User.objects.get(email=email)
                output['username'] = user.username
            return Response(output)
        return Response({'message': 'An email address is required'}, status=400)

    @list_route(permission_classes=[AllowAny])
    def get_reset_code(self, request):
        """
        Get a reset code for an email address and email user
        """
        email = request.query_params.get('email', None)
        if email:
            try:
                user = User.objects.get(email=email)
            except:
                raise ValidationError({'message': 'Email address not in system'})
            else:
                try:
                    exists = ResetCode.objects.get(account__email=email)
                except:
                    pass
                else:
                    exists.delete()
                reset_code = ResetCode(account=user)
                reset_code.save()
                if reset_code.send_email():
                    return Response({'message': 'Email sent'})
                return Response({'message': 'Email failed to send'}, status=500)
        return Response({'message': 'Please provide an email address'}, status=400)

    @list_route(methods=['patch'], permission_classes=[AllowAny])
    def reset_account(self, request):
        """
        Reset a single user account using a generated code
        """
        email = request.data.get('email', None)
        reset_code = request.data.get('code', None)
        new_password = request.data.get('new_password', None)

        if email and new_password and reset_code:
            try:
                reset_data = ResetCode.objects.get(code=reset_code,
                                                   account__email=email)
            except:
                return Response({'message': 'Unable to find a reset for the account'}, status=400)
            else:
                reset_data.account.set_password(new_password)
                reset_data.account.save()
                reset_data.delete()
                return Response({'message': 'Account {} reset'.format(
                                reset_data.account.username)})
        raise ValidationError({'message': 'Please provide email, code and password data'})


class GroupViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    search_fields = ('name',)

    def get_queryset(self):
        if self.request.user.groups.filter(name='admin').exists():
            return Group.objects.all()
        else:
            return self.request.user.groups.all()
