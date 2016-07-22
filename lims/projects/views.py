import django_filters

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, DjangoObjectPermissions

from lims.shared.filters import ListFilter
from lims.permissions.permissions import IsInAdminGroupOrRO

from .models import (Product, ProductStatus, Project)
from .serializers import (ProjectSerializer, ProductSerializer, DetailedProductSerializer,
                          ProductStatusSerializer)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAdminUser, DjangoObjectPermissions,)
    search_fields = ('project_identifier', 'name', 'primary_lab_contact__username')

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(created_by=self.request.user)
        self.assign_permissions(instance, permissions)


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
    filter_class = ProductFilter  # ('project', 'status',)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedProductSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(created_by=self.request.user)
        self.assign_permissions(instance, permissions)


class ProductStatusViewSet(viewsets.ModelViewSet):
    queryset = ProductStatus.objects.all()
    serializer_class = ProductStatusSerializer
    permission_classes = (IsAdminUser, IsInAdminGroupOrRO)
