from django.contrib.auth.models import User

from rest_framework import serializers

from .models import Organism, Trigger, TriggerSet, TriggerAlert, TriggerAlertStatus, \
    TriggerSubscription


class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism
        fields = '__all__'


class TriggerSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerSet
        fields = '__all__'


class TriggerSerializer(serializers.ModelSerializer):
    triggerset_id = serializers.PrimaryKeyRelatedField(
        queryset=TriggerSet.objects.all(), source='triggerset', write_only=True)
    triggerset = TriggerSetSerializer(read_only=True)

    class Meta:
        model = Trigger
        fields = '__all__'


class TriggerAlertSerializer(serializers.ModelSerializer):
    triggerset = TriggerSetSerializer(read_only=True)

    class Meta:
        model = TriggerAlert
        fields = '__all__'


class TriggerAlertStatusSerializer(serializers.ModelSerializer):
    triggeralert = TriggerAlertSerializer(read_only=True)

    class Meta:
        model = TriggerAlertStatus
        fields = '__all__'


class TriggerSubscriptionSerializer(serializers.ModelSerializer):
    triggerset_id = serializers.PrimaryKeyRelatedField(
        queryset=TriggerSet.objects.all(), source='triggerset', write_only=True)
    triggerset = TriggerSetSerializer(read_only=True)
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = TriggerSubscription
        fields = '__all__'
