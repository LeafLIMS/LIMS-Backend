from django.contrib.auth.models import Group
from django.db.models import Model

from guardian.shortcuts import get_groups_with_perms, assign_perm

from rest_framework import serializers
from rest_framework import permissions
from rest_framework import filters


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
