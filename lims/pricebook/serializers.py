from rest_framework import serializers

from .models import PriceBook, Price

class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price

class PriceBookSerializer(serializers.ModelSerializer):
    prices = PriceSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = PriceBook
