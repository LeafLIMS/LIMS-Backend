from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Group

from simple_salesforce import Salesforce

from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import serializers

from lims.shared.pagination import PageNumberPaginationSmall
from lims.shared.mixins import AuditTrailViewMixin

from lims.crm.helpers import CRMCreateProjectFromOrder
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    pagination_class = PageNumberPaginationSmall
    filter_fields = ('complete',)
    search_fields = ('name',)

    def get_queryset(self):
        if (self.request.user.is_superuser or
                Group.objects.get(name="admin") in self.request.user.groups.all()):
            return Order.objects.all()
        else:
            return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            crm_project = CRMCreateProjectFromOrder(self.request,
                                                    serializer.validated_data)
        except:
            raise serializers.ValidationError({'message': 'Could not create the order in CRM'})
        order = serializer.save(user=self.request.user)
        crm_project.order = order
        crm_project.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not settings.TESTMODE:
            sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                            username=settings.SALESFORCE_USERNAME,
                            password=settings.SALESFORCE_PASSWORD,
                            security_token=settings.SALESFORCE_TOKEN)
            try:
                sf.Opportunity.delete(instance.crm.project_identifier)
            except:
                pass
        self.perform_destroy(instance)
        return Response(status=204)

    @list_route()
    def autocomplete(self, request):
        st = request.query_params.get('q', '')
        results = self.get_queryset().filter(Q(name__icontains=st)).order_by('-date_placed')
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @list_route()
    def recent(self, request):
        recent = self.get_queryset().order_by('-date_placed')[:5]
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)

    @list_route()
    def statuses(self, request):
        statuses = [s[1] for s in Order.STATUS_BAR_CHOICES]
        return Response(statuses)
