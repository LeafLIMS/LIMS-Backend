from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Address


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(),
                                        slug_field='username')

    class Meta:
        model = Address
        fields = "__all__"
