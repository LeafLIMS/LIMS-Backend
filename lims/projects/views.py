import csv
import zipfile
import codecs

import django_filters

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route
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

from lims.shared.mixins import StatsViewMixin, AuditTrailViewMixin
from .models import (Product, ProductStatus, Project)
from .serializers import (ProjectSerializer, ProductSerializer,
                          DetailedProductSerializer, ProductStatusSerializer)
from .parsers import DesignFileParser


class ProjectViewSet(AuditTrailViewMixin, ViewPermissionsMixin, StatsViewMixin,
                     viewsets.ModelViewSet):
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
    filter_fields = ('archive', 'crm_project__status', 'primary_lab_contact',)
    search_fields = ('project_identifier', 'name', 'primary_lab_contact__username',
                     'crm_project__account__user__first_name',
                     'crm_project__account__user__last_name',)

    def perform_create(self, serializer):
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save(created_by=self.request.user)
        self.assign_permissions(instance, permissions)

    @detail_route(methods=['POST'])
    def import_products(self, request, pk=None):
        """
        Create products on a project using CSV and ZIP files.
        """
        # Two files to import: CSV and ZIP of products
        # Parse CSV
        # Unzip designs
        # Go through CSV file, creating products
        # For each product parse the design
        # Return list of created projects + failures
        products_file = request.data.get('products_file')
        designs_file = request.data.get('designs_file')

        rejected = []
        completed = []

        if products_file:
            # Read the CSV file of products into a list
            decoded_file = codecs.iterdecode(products_file, 'utf-8')
            products = [line for line in csv.DictReader(decoded_file, skipinitialspace=True)]
            # Open the zip file for reading, assign the files within to a dict with filenames
            designs = {}
            if designs_file:
                with zipfile.ZipFile(designs_file, 'r') as dzip:
                    for file_path in dzip.namelist():
                        filename = file_path.split('/')[-1]
                        with dzip.open(file_path) as d:
                            designs[filename] = d.read()
            # Iteratre through products creating them and linking design
            for p in products:
                # Replace the name of the design file with the actual contents
                if p.get('design', None):
                    p['design'] = designs[p['design']].decode('UTF-8')
                p['project'] = self.get_object().id
                serializer = ProductSerializer(data=p)
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    items = []
                    parser = DesignFileParser(instance.design)
                    if instance.design_format == 'csv':
                        items = parser.parse_csv()
                    elif instance.design_format == 'gb':
                        items = parser.parse_gb()
                    for i in items:
                        instance.linked_inventory.add(i)
                    completed.append(p)
                else:
                    p['reason'] = serializer.errors
                    rejected.append(p)
            return Response({'message': 'Import completed',
                             'completed': completed,
                             'rejected': rejected})
        else:
            return Response({'message': 'Please supply a product definition and file of designs'},
                            status=400)


class ProductFilter(django_filters.FilterSet):
    id__in = ListFilter(name='id')
    on_run = django_filters.MethodFilter()

    def filter_on_run(self, queryset, value):
        if value == 'False':
            return queryset.exclude(runs__is_active=True)
        elif value == 'True':
            return queryset.filter(runs__is_active=True)
        return queryset

    class Meta:
        model = Product
        fields = {
            'id': ['exact', 'in'],
            'project': ['exact'],
            'status': ['exact'],
            'on_run': ['exact'],
        }


class ProductViewSet(AuditTrailViewMixin, ViewPermissionsMixin, StatsViewMixin,
                     viewsets.ModelViewSet):
    """
    Provides a list of all products
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (ExtendedObjectPermissions,)
    filter_backends = (SearchFilter, DjangoFilterBackend,
                       OrderingFilter, ExtendedObjectPermissionsFilter,)
    search_fields = ('product_identifier', 'name', 'product_type__name',)
    filter_class = ProductFilter

    def _parse_design(self, instance):
        """
        Takes a design file and extracts the necessary info
        out to add inventory items or other things.
        """
        if instance.design is not None:
            items = []
            parser = DesignFileParser(instance.design)
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
        if ('change_project' in get_group_perms(self.request.user, project)
                or self.request.user.groups.filter(name='admin').exists()):
            instance = serializer.save(created_by=self.request.user)
            self.clone_group_permissions(instance.project, instance)
        else:
            raise ValidationError('You do not have permission to create this')
        # Does it have a design?
        # If so, parse the design to extract info to get parts from
        # inventory.
        self._parse_design(instance)


class ProductStatusViewSet(AuditTrailViewMixin, viewsets.ModelViewSet):
    queryset = ProductStatus.objects.all()
    serializer_class = ProductStatusSerializer
    permission_classes = (IsInAdminGroupOrRO,)
