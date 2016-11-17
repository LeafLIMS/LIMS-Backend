from rest_framework import serializers

from lims.crm.serializers import CRMProjectSerializer
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    crm = CRMProjectSerializer(read_only=True)

    class Meta:
        model = Order
