from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from .models import CopyFileDriver
from .serializers import CopyFileDriverSerializer


class CopyFileDriverViewSet(viewsets.ModelViewSet):
    queryset = CopyFileDriver.objects.all()
    serializer_class = CopyFileDriverSerializer

    @detail_route(methods=['GET'])
    def test(self, request, pk=None):
        fd = self.get_object()
        int_dict = {
            'project_identifier': 'PI12345',
            'product_identifier': 'PRO12345',
            'run_identifier': '12345-67890-12345-567-987',
            }
        for cpth in fd.locations.all():
            print(cpth.copy_to_path(int_dict))
            print(cpth.copy_from_path(int_dict))
        return Response('')
