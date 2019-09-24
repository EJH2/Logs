from rest_framework import permissions


class HasAPIAccess(permissions.BasePermission):
    """
    Custom permission to only allow users with API access.
    """

    def has_permission(self, request, view):
        return all([request.user, request.user.is_authenticated, request.user.has_perm('api.api_access')])
