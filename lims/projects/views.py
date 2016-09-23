import django_filters

from rest_framework import viewsets
from rest_framework.validators import ValidationError
from rest_framework.filters import (OrderingFilter,
                                    SearchFilter,
                                    DjangoFilterBackend)

from guardian.shortcuts import get_group_perms

from lims.shared.filters import ListFilter
from lims.permissions.permissions import (IsInAdminGroupOrRO,
                                          ViewPermissionsMixin,
                                          ExtendedObjectPermissions,
                                          ExtendedObjectPermissionsFilter)

from .models import (Product, ProductStatus, Project)
from .serializers import (ProjectSerializer, ProductSerializer,
                          DetailedProductSerializer, ProductStatusSerializer)
from .parsers import DesignFileParser


class ProjectViewSet(ViewPermissionsMixin, viewsets.ModelViewSet):
    """
    View all projects the user has permissions for

    Projects are filtered by permissions and users cannot see any
    projects they do not have permissions for.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)
    search_fields = ('project_identifier', 'name', 'primary_lab_contact__username')

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(created_by=self.request.user)
        self.assign_permissions(instance, permissions)


class ProductFilter(django_filters.FilterSet):
    # on_workflow_as = django_filters.MethodFilter()
    id__in = ListFilter(name='id')

    def filter_on_workflow_as(self, queryset, value):
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
            # 'on_workflow_as': ['exact'],
        }


class ProductViewSet(ViewPermissionsMixin, viewsets.ModelViewSet):
    """
    Provides a list of all products
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)
    search_fields = ('product_identifier', 'name',)
    filter_class = ProductFilter

    def _parse_design(self, instance):
        """
        Takes a design file and extracts the necessary info
        out to add inventory items or other things.
        """
        if instance.design is not None:
            items = []
            parser = DesignFileParser(data=instance.design)
            if instance.design_format == 'csv':
                items = parser.parse_csv()
            elif instance.design_format == 'gb':
                items = parser.parse_gb()
            for i in items:
                instance.linked_inventory.add(i)

    def get_serializer_class(self):
        # Use a more compact serializer when listing.
        # This makes things run more efficiantly.
        if self.action == 'retrieve':
            return DetailedProductSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        # Ensure the user has the correct permissions on the Project
        # to add a product to it.
        project = serializer.validated_data['project']
        if 'view_project' in get_group_perms(self.request.user, project):
            instance = serializer.save(created_by=self.request.user)
            self.clone_group_permissions(instance.project, instance)
        else:
            raise ValidationError('You do not have permission to create this')
        # Does it have a design?
        # If so, parse the design to extract info to get parts from
        # inventory.
        self._parse_design(instance)


class ProductStatusViewSet(viewsets.ModelViewSet):
    queryset = ProductStatus.objects.all()
    serializer_class = ProductStatusSerializer
    permission_classes = (IsInAdminGroupOrRO,)
