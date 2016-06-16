import django_filters
from django_filters import Filter
from django_filters.fields import Lookup

from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAdminUser, DjangoObjectPermissions
from rest_framework.parsers import MultiPartParser, FormParser

from lims.shared.filters import ListFilter

from .models import (Product, ProductStatus, Project, Comment, WorkLog) 
from .serializers import *

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)
    search_fields = ('project_identifier', 'name', 'primary_lab_contact__username')

class ProductFilter(django_filters.FilterSet):
    on_workflow = django_filters.MethodFilter()
    id__in = ListFilter(name='id')

    def filter_on_workflow(self, queryset, value):
        if value == 'False':
            return queryset.filter(on_workflow_as__isnull=True)
        elif value == 'True':
            return queryset.filter(on_workflow_as__isnull=False)
        return queryset

    class Meta:
        model = Product
        fields = {
            'id': ['exact', 'in'],
            'project': ['exact'], 
            'status': ['exact'], 
            'on_workflow_as': ['exact'],
        }

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)
    search_fields = ('product_identifier', 'name',)
    filter_class = ProductFilter #('project', 'status',)

    def get_serializer_class(self):
        '''
        if hasattr(self.request, 'query_params'):
            extra = self.request.query_params.get('extra', None)
            if self.action == 'retrieve':
                return DetailedProductSerializer
        '''
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        request.data['created_by'] = request.user.username 
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class ProductStatusViewSet(viewsets.ModelViewSet):
    queryset = ProductStatus.objects.all()
    serializer_class = ProductStatusSerializer
