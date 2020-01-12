from allauth.socialaccount.models import SocialAccount
from rest_framework import permissions


class HasAPIAccess(permissions.BasePermission):
    """
    Custom permission to only allow users with API access.
    """

    def has_permission(self, request, view):
        return all([request.user, request.user.is_authenticated, request.user.has_perm('api.api_access')])


def filter_queryset(request, queryset):
    try:
        discord_user = SocialAccount.objects.get(user=request.user)
        guilds = discord_user.extra_data.get('guilds', [])
        return queryset.filter(owner=request.user) | queryset.filter(guild__in=[
            # Check if user is owner of guild or has manage messages perm
            int(g['id']) for g in guilds if g['owner'] or (g['permissions'] >> 13) & 1
        ])
    except SocialAccount.DoesNotExist:
        return queryset.filter(owner=request.user)
