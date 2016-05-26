from rest_framework import serializers

from .models import CRMAccount, CRMProject, CRMQuote

class CRMAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRMAccount

class CRMQuoteSerializer(serializers.ModelSerializer):
    quote_url = serializers.ReadOnlyField()
    class Meta:
        model = CRMQuote

class CRMProjectSerializer(serializers.ModelSerializer):
    quotes = CRMQuoteSerializer(many=True, read_only=True)
    class Meta:
        model = CRMProject
