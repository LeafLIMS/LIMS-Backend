from django.contrib.auth.models import Group
from django.db.models import Model

from guardian.shortcuts import (get_groups_with_perms, assign_perm, remove_perm,
                                get_perms)

from rest_framework import serializers
from rest_framework import permissions
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import detail_route


class IsSuperUser(permissions.BasePermission):
    """
    Limit all access to superuser only
    """
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsThisUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff


class IsAddressOwner(permissions.BasePermission):
    """
    Is this address being edited by user or admin
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated():
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated():
            has_group = request.user.groups.filter(name='admin').exists()
            if obj.user == request.user or has_group:
                return True
        return False


class IsAddressOwnerFilter(filters.BaseFilterBackend):
    """
    Show only user address or all if admin
    """

    def filter_queryset(self, request, queryset, view):
        has_group = request.user.groups.filter(name='admin').exists()
        if has_group:
            return queryset
        else:
            return queryset.filter(user=request.user)


class IsInGroupOrRO(permissions.BasePermission):
    """
    Limit write access to user in a specified group
    """
    group_name = 'user'

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated():
            has_group = request.user.groups.filter(name=self.group_name).exists()
            if request.method in permissions.SAFE_METHODS or has_group:
                return True
        return False


class IsInStaffGroupOrRO(IsInGroupOrRO):
    """
    Limit write access to user in staff group
    """
    group_name = 'staff'


class IsInAdminGroupOrRO(IsInGroupOrRO):
    """
    Limit write access to user in admin group
    """
    group_name = 'admin'


class ExtendedObjectPermissionsFilter(filters.DjangoObjectPermissionsFilter):
    """
    Allow admin group users full access to all items
    """

    def filter_queryset(self, request, queryset, view):
        # If we're the admin group allow access otherwise test
        # for the correct permissions.
        if request.user.groups.filter(name='admin').exists():
            return queryset
        return super(ExtendedObjectPermissionsFilter, self).filter_queryset(
                request, queryset, view)


class ExtendedObjectPermissions(permissions.DjangoObjectPermissions):
    """
    Extends object permissions to include 'view' for GET/HEAD/OPTIONS

    Allows admin group users full access to all items.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_permission(self, request, view):
        # If we're the admin group allow access otherwise test
        # for the correct permissions.
        if request.user.groups.filter(name='admin').exists():
            return True
        return super(ExtendedObjectPermissions, self).has_permission(
                request, view)

    def has_object_permission(self, request, view, obj):
        # If we're the admin group allow access otherwise test
        # for the correct permissions.
        if request.user.groups.filter(name='admin').exists():
            return True
        return super(ExtendedObjectPermissions, self).has_object_permission(
                request, view, obj)


class SerializerPermissionsMixin(serializers.Serializer):
    """
    Mixin to add fields to serializer for add/list of permissions
    """
    # A dict of permissions that indicate which groups
    # can and cannot edit this object.
    permissions = serializers.SerializerMethodField()
    # A dict of groups -> permission string with the signature
    # rw (read/write). Write allows editing as the user already
    # has to have permissions to create an instance
    # example: {"admin": "rw", "staff": "r"}
    assign_groups = serializers.DictField(allow_null=True,
                                          write_only=True)

    def get_permissions(self, obj):
        # These are used for display/editing and are not
        # used to actually limit anything, that is done
        # in the view
        perms = {}
        if isinstance(obj, Model):
            for grp, p in get_groups_with_perms(obj, attach_perms=True).items():
                perms[grp.name] = p
        return perms


class SerializerReadOnlyPermissionsMixin(SerializerPermissionsMixin):
    """
    As SerializerPermissionsMixin but with assign_groups read only
    """
    assign_groups = serializers.ReadOnlyField()


class ViewPermissionsMixin():

    PERM_TEMPLATE = (
        'add_{}',
        'change_{}',
        'delete_{}',
        'view_{}',
    )

    def clean_serializer_of_permissions(self, serializer):
        """
        Remove assign_groups from serializer before it is saved
        """
        permissions = serializer.validated_data.get('assign_groups', {})
        serializer.validated_data.pop('assign_groups', None)
        # We need to revalidate to recreate the serialized instance
        # But as we know it's already valid just ignore the output
        serializer.is_valid()
        return serializer, permissions

    def current_permissions(self, group, instance):
        """
        Get permissions for group on this instance

        Returns a string of 'rw' for change and 'r' for
        view only.
        """
        model_name = instance._meta.model_name
        current_permissions = get_perms(group, instance)
        if 'change_{}'.format(model_name) in current_permissions:
            return 'rw'
        return 'r'

    def remove_group_permissions(self, instance, group):
        """
        Remove permissions from instance for group
        """
        model_name = instance._meta.model_name
        for perm in self.PERM_TEMPLATE:
            remove_perm(perm.format(model_name), group, instance)
        return True

    def assign_permissions(self, instance, permissions):
        """
        Assign the relevant permissions to a user for an object

        Can be used to change permissions from rw/r and vice versa
        """
        model_name = instance._meta.model_name
        for group, perm in permissions.items():
            try:
                grp = Group.objects.get(name=group)
            except Group.DoesNotExist:
                return False
            current_permission = self.current_permissions(grp, instance)
            if perm == 'rw':
                # Give read and write permissions
                # Iterate through templates and build the
                # permission codename based on model name
                for pt in self.PERM_TEMPLATE:
                    assign_perm(pt.format(model_name), grp, instance)
            else:
                # Only give read permissions
                if current_permission == 'rw':
                    self.remove_group_permissions(instance, grp)
                assign_perm('view_%s' % model_name, grp, instance)
        return True

    def clone_group_permissions(self, clone_from, clone_to):
        """
        Takes group permissions from one object and applies to another

        This will translate model names so can match permissions of e.g.
        a Project to that of its child Products
        """
        # NEED TO CHECK IF MEMBER OF AT LEAST ONE GROUP BEFORE CLONE!!!!
        permissions = get_groups_with_perms(clone_from, attach_perms=True)
        model_name = clone_to._meta.model_name
        for group, perms in permissions.items():
            for p in perms:
                # Split permission to get operator e.g. change
                operator = p.split('_')[0]
                assign_perm('{}_{}'.format(operator, model_name), group, clone_to)

    def perform_create(self, serializer):
        """
        By default override perform_create to add permissions

        Most of the views actually have a perform_create function already
        in place so this is more of a template.
        """
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save()
        self.assign_permissions(instance, permissions)

    @detail_route(methods=['PATCH'])
    def set_permissions(self, request, pk=None):
        """
        Set permissions on the object provided.

        Permissions in the same format as assign_groups field
        on the SerializerPermissionsMixin.
        """
        # TODO: watch on set permission to change child permissions?
        # Could look for parent id or something?
        obj = self.get_object()
        try:
            permissions = request.data
        except:
            return Response({'message': 'Please provide permissions in correct format'}, status=400)
        if permissions:
            if self.assign_permissions(obj, permissions):
                return Response({'message': 'Permissions set for {}'.format(obj)})
            else:
                return Response({'message': 'Permission set failure, check group'}, status=400)
        return Response({'message': 'Please provide a list of permissions'}, status=400)

    @detail_route(methods=['DELETE'])
    def remove_permissions(self, request, pk=None):
        obj = self.get_object()
        groups_to_remove = request.query_params.getlist('groups', None)
        if groups_to_remove:
            model_name = obj._meta.model_name
            for g in groups_to_remove:
                try:
                    group = Group.objects.get(name=g)
                except Group.DoesNotExist:
                    return Response({'message': 'Group does not exist'})
                for perm in self.PERM_TEMPLATE:
                    remove_perm(perm.format(model_name), group, obj)
            return Response({'message': '{} groups removed'.format(len(groups_to_remove))})
        return Response({'message': 'Please provide a list of groups'}, status=400)
