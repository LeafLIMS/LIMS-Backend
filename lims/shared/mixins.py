from django.db.models import Count
from django.core.exceptions import FieldError

from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.serializers import ValidationError


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
