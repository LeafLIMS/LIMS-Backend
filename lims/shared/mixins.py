from django.db.models import Count
from reversion.models import Version
from django.core.exceptions import FieldError
import datetime
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.serializers import ValidationError
from rest_framework.exceptions import PermissionDenied


class StatsViewMixin(viewsets.ViewSet):
    """
    Provide API endpoint for basic stats on queryset
    """

    @list_route()
    def stats(self, request):
        """
        Query a field for stats on contents
        """
        field = request.query_params.get('field', None)

        if field:
            qs = self.get_queryset()
            try:
                counts = qs.values(field).annotate(Count(field)).order_by()
            except FieldError:
                raise ValidationError({'message': 'You must supply a valid field'})
            return Response(counts)
        raise ValidationError({'message': 'You must supply a field for stats'})


class AuditTrailViewMixin(viewsets.ViewSet):
    """
    Provide API endpoints for audit trails. Permissions should be inherited from the views.
    """

    @detail_route(methods=['GET'])
    def history(self, request, pk=None):
        instance = self.get_object()
        user = request.query_params.get('user', None)  # Default to all users
        start = request.query_params.get('start', None)  # In YYYY-MM-DD format
        if start:
            start = datetime.datetime.strptime(start, '%Y-%m-%d')
        else:
            start = datetime.datetime.min
        start = timezone.make_aware(start, timezone.get_default_timezone())
        end = request.query_params.get('end', None)  # In YYYY-MM-DD format
        if end:
            end = datetime.datetime.strptime(start, '%Y-%m-%d')
        else:
            end = datetime.datetime.today()
        end = timezone.make_aware(end, timezone.get_default_timezone())
        history = []
        for v, version in enumerate(Version.objects.get_for_object(instance).reverse()):
            if (user is not None and version.revision.user.username != user) \
                    or version.revision.date_created < start \
                    or version.revision.date_created > end:
                continue
            history.append({'version': v,
                            'created': version.revision.date_created.strftime('%Y-%m-%d %H:%M:%S'),
                            'user': version.revision.user.username,
                            'data': version.field_dict})
        return Response(history, status=200)

    @detail_route(methods=['GET'])
    def compare(self, request, pk=None):
        instance = self.get_object()
        version1 = request.query_params.get('version1', -1)  # 0-index, current is last in list
        version2 = request.query_params.get('version2', None)  # 0-index, fail if not provided
        if version2 is None:
            return Response({'message': 'Must provide value for version2'}, status=400)
        versions = Version.objects.get_for_object(instance).reverse()
        v1 = versions[int(version1)]
        v2 = versions[int(version2)]
        # Return a list of fields that differ between the two versions. Omitted fields are equal.
        # Each field has a 'version1' and 'version2' entry to show before/after effect.
        # Fields present in only one version are marked ##MISSING## in the other.
        changes = {}
        # First check all fields in v1. Only record those that differ.
        for field, v1_value in v1.field_dict.items():
            if field in v2.field_dict:
                if v2.field_dict[field] != v1_value:
                    changes[field] = {'version1': v1_value, 'version2': v2.field_dict[field]}
            else:
                changes[field] = {'version1': v1_value, 'version2': '##MISSING##'}
        # Now add in any fields in v2 that were not in v1
        for field, v2_value in v2.field_dict.items():
            if field not in v1.field_dict:
                changes[field] = {'version1': '##MISSING##', 'version2': v2_value}
        return Response(changes, status=200)

    @detail_route(methods=['POST'])
    def revert(self, request, pk=None):
        # Admin only
        if not self.request.user.groups.filter(name='admin').exists():
            raise PermissionDenied()
        instance = self.get_object()
        version = request.query_params.get('version', None)  # 0-index, fail if not provided
        if version is None:
            return Response({'message': 'Must provide value for version'}, status=400)
        versions = Version.objects.get_for_object(instance).reverse()
        versions[int(version)].revision.revert(delete=True)
        instance.refresh_from_db()
        return Response(status=200)
