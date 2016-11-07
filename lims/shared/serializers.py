from rest_framework import serializers

from .models import Organism, Trigger, TriggerSet, TriggerAlert, TriggerAlertStatus, \
    TriggerSubscription


class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism


class TriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trigger


class TriggerSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerSet


class TriggerAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerAlert


class TriggerAlertStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerAlertStatus


class TriggerSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerSubscription
