from rest_framework import serializers

from .models import Organism, Trigger, TriggerSet, TriggerAlert, TriggerAlertStatus, \
    TriggerSubscription


class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism


class TriggerSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerSet


class TriggerSerializer(serializers.ModelSerializer):
    triggerSet = TriggerSetSerializer(read_only=True)

    class Meta:
        model = Trigger


class TriggerAlertSerializer(serializers.ModelSerializer):
    triggerSet = TriggerSetSerializer(read_only=True)

    class Meta:
        model = TriggerAlert


class TriggerAlertStatusSerializer(serializers.ModelSerializer):
    triggerAlert = TriggerAlertSerializer(read_only=True)

    class Meta:
        model = TriggerAlertStatus


class TriggerSubscriptionSerializer(serializers.ModelSerializer):
    triggerSet = TriggerSetSerializer(read_only=True)

    class Meta:
        model = TriggerSubscription
