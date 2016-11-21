from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route
from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework.filters import DjangoFilterBackend
from rest_framework.serializers import ValidationError
import datetime

from lims.permissions.permissions import IsInAdminGroupOrRO
from lims.shared.mixins import AuditTrailViewMixin

from .models import Organism, TriggerSet, Trigger, TriggerAlertStatus, TriggerSubscription
from .serializers import OrganismSerializer, TriggerSerializer, TriggerSubscriptionSerializer, \
    TriggerAlertStatusSerializer, TriggerSetSerializer


class OrganismViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = Organism.objects.all()
    serializer_class = OrganismSerializer
    search_fields = ('name', 'common_name',)
    permission_classes = (IsInAdminGroupOrRO,)


class TriggerSetViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = TriggerSet.objects.all()
    serializer_class = TriggerSetSerializer
    permission_classes = (IsInAdminGroupOrRO,)
    filter_backends = (DjangoFilterBackend,)

    @detail_route()
    def triggers(self, request, pk=None):
        triggerset = self.get_object()
        serializer = TriggerSerializer(triggerset.triggers.all(), many=True)
        return Response(serializer.data)

    @detail_route()
    def subscriptions(self, request, pk=None):
        triggerset = self.get_object()
        serializer = TriggerSubscriptionSerializer(triggerset.subscriptions.all(), many=True)
        return Response(serializer.data)


class TriggerViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = Trigger.objects.all()
    serializer_class = TriggerSerializer
    permission_classes = (IsInAdminGroupOrRO,)


class TriggerSubscriptionViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    serializer_class = TriggerSubscriptionSerializer
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        if self.request.user.is_superuser or \
                        Group.objects.get(name="admin") in self.request.user.groups.all():
            return TriggerSubscription.objects.all()
        else:
            return TriggerSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Allow an admin user to set the user but otherwise can only create own subscriptions
        if self.request.user.groups.filter(name='admin').exists() or self.request.user == \
                serializer.validated_data['user']:
            serializer.save()
        else:
            raise ValidationError('You cannot add a subscription to another user')


class TriggerAlertStatusViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                                viewsets.GenericViewSet):  # NB No create, edit, or delete
    serializer_class = TriggerAlertStatusSerializer
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        if self.request.user.is_superuser or \
                        Group.objects.get(name="admin") in self.request.user.groups.all():
            return TriggerAlertStatus.objects.all()
        else:
            return TriggerAlertStatus.objects.filter(user=self.request.user)

    @detail_route(methods=['DELETE'])
    def silence(self, request, pk=None):
        # Check have permissions
        alertstatus = self.get_object()
        if alertstatus is None:
            return Response(status=404)
        if not alertstatus.user == self.request.user and \
                not self.request.user.is_superuser and \
                not Group.objects.get(name="admin") in self.request.user.groups.all():
            return Response(status=403)
        # Silence for this user only
        alertstatus.status = TriggerAlertStatus.SILENCED
        alertstatus.last_updated_by = request.user
        alertstatus.last_updated = datetime.datetime.now()
        alertstatus.save()
        return Response(status=204)

    @detail_route(methods=['DELETE'])
    def dismiss(self, request, pk=None):
        alertstatus = self.get_object()
        if alertstatus is None:
            return Response(status=404)
        if not alertstatus.user == self.request.user and \
                not self.request.user.is_superuser and \
                not Group.objects.get(name="admin") in self.request.user.groups.all():
            return Response(status=403)
        # Dismiss for all users that have not already silenced this alert
        for related_alert in alertstatus.triggeralert.statuses.all():
            if related_alert.status == TriggerAlertStatus.ACTIVE:
                related_alert.status = TriggerAlertStatus.DISMISSED
                related_alert.last_updated_by = request.user
                related_alert.last_updated = datetime.datetime.now()
                related_alert.save()
        return Response(status=204)
