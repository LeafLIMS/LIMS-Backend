from django.contrib.auth.models import User, Group, Permission
from django.conf import settings

from rest_framework import serializers
from rest_framework.utils import model_meta

from lims.addressbook.serializers import AddressSerializer
from lims.crm.serializers import CRMAccountSerializer


class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True) 
    groups = serializers.SlugRelatedField(queryset=Group.objects.all(), 
            many=True, slug_field='name', required=False)

    crmaccount = CRMAccountSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'password', 'username',
                  'first_name', 'last_name', 'groups',
                  'email', 'addresses', 'crmaccount')
        read_only_fields = ('id', 'addresses', 'crmaccount', 'groups',)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        try:
            instance = ModelClass(**validated_data)
            instance.set_password(validated_data['password'])
            instance.save()
        except TypeError as exc:
            msg = (
                'Got a `TypeError` when calling `%s.objects.create()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.objects.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception text was: %s.' %
                (
                    ModelClass.__name__,
                    ModelClass.__name__,
                    self.__class__.__name__,
                    exc
                )
            )
            raise TypeError(msg)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                setattr(instance, field_name, value)

        # All users are automatically added to the user group.
        # The user is created on boot so no try.
        group = Group.objects.get(name='user')
        instance.groups.add(group)

        return instance


class StaffUserSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        fields = ('id', 'password', 'is_superuser', 'username',
                  'first_name', 'last_name',
                  'email', 'is_staff', 'groups',
                  'addresses', 'crmaccount')
        read_only_fields = ('id', 'is_superuser', 'addresses', 'crmaccount',)


class SuperUserSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        fields = ('id', 'password', 'is_superuser', 'username',
                  'first_name', 'last_name',
                  'email', 'is_staff', 'groups',
                  'addresses', 'crmaccount')
        read_only_fields = ('id', 'addresses', 'crmaccount',)


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(queryset=Permission.objects.all(),
                                               many=True, slug_field='name', required=False)

    class Meta:
        model = Group


class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
