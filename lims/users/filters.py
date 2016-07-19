from rest_framework import filters


class IsOwnerFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_staff:
            return queryset
        else:
            return queryset.filter(user=request.user)
