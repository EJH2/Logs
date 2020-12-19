from allauth.socialaccount.models import SocialAccount
from rest_framework import permissions


class HasAPIAccess(permissions.BasePermission):
    """
    Custom permission to only allow users with API access.
    """

    def has_permission(self, request, view):
        return all([request.user, request.user.is_authenticated, request.user.has_perm('api.api_access')])


def filter_queryset(request, queryset):
    if not request.user.is_authenticated:
        return queryset.none()
    try:
        discord_user = SocialAccount.objects.get(user=request.user)
        guilds = discord_user.extra_data.get('guilds', [])
        return queryset.filter(owner=request.user) | queryset.filter(guild__in=[
            # Check if user is owner of guild or has manage messages perm
            int(g['id']) for g in guilds if g['owner'] or (g['permissions'] >> 13) & 1
        ])
    except SocialAccount.DoesNotExist:
        return queryset.filter(owner=request.user)


def filter_view_queryset(request, queryset):
    if not request.user.is_authenticated:
        return queryset.none()
    if request.user.is_staff:
        return queryset.all()
    try:
        discord_user = SocialAccount.objects.get(user=request.user)
        _guilds = discord_user.extra_data.get('guilds', [])
        guilds = [int(g['id']) for g in _guilds]
        mod_guilds = [
            # Check if user is owner of guild or has manage messages perm
            int(g['id']) for g in _guilds if g['owner'] or (g['permissions'] >> 13) & 1
        ]
        return queryset.filter(privacy='public') | queryset.filter(guild__in=guilds, privacy='guild') | \
            queryset.filter(guild__in=mod_guilds, privacy='mods')
    except SocialAccount.DoesNotExist:
        return queryset.filter(privacy='public')
