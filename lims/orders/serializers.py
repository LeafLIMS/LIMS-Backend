from django.contrib.auth.models import User

from rest_framework import serializers

from lims.users.serializers import UserSerializer 
from lims.crm.serializers import CRMQuoteSerializer, CRMProjectSerializer
from .models import Order, Service

class OrderSerializer(serializers.ModelSerializer):
    services = serializers.SlugRelatedField(
            many=True, 
            queryset=Service.objects.all(),
            slug_field='name')
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    crm = CRMProjectSerializer(read_only=True)

    class Meta:
        model = Order
