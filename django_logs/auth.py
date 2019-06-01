from enum import Enum

from allauth.socialaccount.models import SocialAccount


class PermissionType(Enum):
    administrator = 1
    ban_members = 2
    kick_members = 3
    manage_guild = 4
    manage_channels = 5
    view_audit_log = 6
    manage_messages = 7

    def __int__(self):
        return self.value

    def __repr__(self):
        return self.name.replace('_', ' ').title()


permission_enums = {
    'kick_members': 1,
    'ban_members': 2,
    'administrator': 3,
    'manage_channels': 4,
    'manage_guild': 5,
    'view_audit_log': 7,
    'manage_messages': 13,
}


class Permissions:
    __slots__ = ('value',)

    def __init__(self, permissions=0):
        if not isinstance(permissions, int):
            raise TypeError('Expected int parameter, received %s instead.' % permissions.__class__.__name__)

        self.value = permissions

    def has_perm(self, index):
        if bool((self.value >> permission_enums.get('administrator', 0)) & 1):
            return True
        return bool((self.value >> permission_enums.get(PermissionType(index).name, 0)) & 1)


def user_has_permission(user, permissions: list, guild_id: int, any_or_all):
    if not user.is_authenticated:
        return False

    try:
        social = SocialAccount.objects.get(user=user)
    except SocialAccount.DoesNotExist:
        return True

    guilds = social.extra_data['guilds']
    guild = [g for g in guilds if g['id'] == guild_id]
    if not guild:
        return False

    guild = guild[0]
    user_perms = Permissions(guild['permissions'])
    total_perms = []
    for permission in permissions:
        total_perms.append(user_perms.has_perm(permission))

    return any_or_all(total_perms)


def filter_query(request, queryset):
    if request.user.is_staff:
        return queryset
    m_logs = queryset.filter(guild_id__isnull=False)
    mod_logs = [log.short_code for log in m_logs if user_has_permission(request.user, [1, 5, 7], log.guild_id, any)]
    return queryset.filter(author=request.user) | queryset.filter(short_code__in=mod_logs)
