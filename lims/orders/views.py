
from django.conf import settings
from django.db.models import Q

from simple_salesforce import Salesforce

from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from lims.shared.pagination import PageNumberPaginationSmall

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    pagination_class = PageNumberPaginationSmall

    def get_queryset(self):
        if self.request.user.is_superuser or 'admin' in self.request.user.groups.all():
            return Order.objects.all()
        else:
            return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if serializer.validated_data['user'] is None:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=serializer.validated_data['user'])

    def destroy(self, request, *args, **kwargs):
        sf = Salesforce(instance_url=settings.SALESFORCE_URL,
                        username=settings.SALESFORCE_USERNAME,
                        password=settings.SALESFORCE_PASSWORD,
                        security_token=settings.SALESFORCE_TOKEN)
        instance = self.get_object()
        try:
            sf.Opportunity.delete(instance.crm.project_identifier)
        except:
            pass
        self.perform_destroy(instance)
        return Response(status=204)

    @list_route()
    def autocomplete(self, request):
        st = request.query_params.get('q', '')
        results = self.get_queryset().filter(Q(name__icontains=st))
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @list_route()
    def recent(self, request):
        if request.user.is_staff:
            recent = Order.objects.all().order_by('-date_placed')[:5]
        else:
            recent = Order.objects.filter(user=request.user).order_by('-date_placed')[:5]
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)

    @list_route()
    def statuses(self, request):
        statuses = [s[1] for s in Order.STATUS_BAR_CHOICES]
        return Response(statuses)
