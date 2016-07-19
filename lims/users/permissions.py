from rest_framework import permissions


class UserIsOwnerAccessOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsThisUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff


class IsSuperUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_superuser
