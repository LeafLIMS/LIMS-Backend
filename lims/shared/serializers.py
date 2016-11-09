from rest_framework import serializers

from .models import Organism, Trigger, TriggerSet, TriggerAlert, TriggerAlertStatus, \
    TriggerSubscription


class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism


class TriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trigger
        depth = 1


class TriggerSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerSet
        depth = 1


class TriggerAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerAlert
        depth = 2


class TriggerAlertStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerAlertStatus
        depth = 3


class TriggerSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerSubscription
        depth = 2
