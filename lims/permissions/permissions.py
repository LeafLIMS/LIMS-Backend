from django.contrib.auth.models import Group

from guardian.shortcuts import get_groups_with_perms, assign_perm

from rest_framework import serializers
from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Limit all access to superuser only
    """
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsThisUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff


class IsInStaffGroupOrRO(permissions.BasePermission):
    """
    Limit write access to user in staff group
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            if request.user.groups.filter('staff').exists():
                return True
            return False


class IsInAdminGroupOrRO(permissions.BasePermission):
    """
    Limit write access to user in admin group
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            if request.user.groups.filter(name='admin').exists():
                return True
            return False


class ExtendedObjectPermissions(permissions.DjangoObjectPermissions):
    """
    Extends permissions to include 'view' for GET/HEAD/OPTIONS
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


class SerializerPermissionsMixin(serializers.Serializer):

    # A dict of permissions that indicate which groups
    # can and cannot edit this object.
    permissions = serializers.SerializerMethodField()
    # A dict of groups -> permission string with the signature
    # rw (read/write). Write allows editing as the user already
    # has to have permissions to create an instance
    assign_groups = serializers.DictField(allow_null=True,
                                          write_only=True)

    def get_permissions(self, obj):
        # These are used for display/editing and are not
        # used to actually limit anything, that is done
        # in the view
        perms = {}
        for grp, p in get_groups_with_perms(obj, attach_perms=True).items():
            perms[grp.name] = p
        return perms


class ViewPermissionsMixin():

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

    def assign_permissions(self, instance, permissions):
        """
        Assign the relevant permissions to a user for an object
        """
        perm_template = (
            'change_{}',
            'delete_{}',
            'view_{}',
        )
        model_name = instance._meta.model_name
        for group, perm in permissions.items():
            grp = Group.objects.get(name=group)
            if perm == 'rw':
                # Give read and write permissions
                # Iterate through templates and build the
                # permission codename based on model name
                for pt in perm_template:
                    assign_perm(pt.format(model_name), grp, instance)
            else:
                # Only give read permissions
                assign_perm('view_%s' % model_name, grp, instance)

    def perform_create(self, serializer):
        """
        By default override perform_create to add permissions
        """
        serializer, permissions = self.clean_serializer_of_permissions(serializer)
        instance = serializer.save()
        self.assign_permissions(instance, permissions)
