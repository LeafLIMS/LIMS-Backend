from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route
from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework.filters import DjangoFilterBackend

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

    @detail_route()
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
        alertstatus.save()
        return Response(status=204)

    @detail_route()
    def dismiss(self, request, pk=None):
        alertstatus = self.get_object()
        if alertstatus is None:
            return Response(status=404)
        if not alertstatus.user == self.request.user and \
                not self.request.user.is_superuser and \
                not Group.objects.get(name="admin") in self.request.user.groups.all():
            return Response(status=403)
        # Dismiss for all users that have not already silenced this alert
        for relatedAlert in alertstatus.triggerAlert.statuses.all():
            if relatedAlert.status == TriggerAlertStatus.ACTIVE:
                relatedAlert.status = TriggerAlertStatus.DISMISSED
                relatedAlert.save()
        return Response(status=204)
