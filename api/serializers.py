from allauth.socialaccount.models import SocialAccount
from rest_framework import serializers

from django_logs.models import Log


class LogSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    guild_id = serializers.SerializerMethodField()

    @staticmethod
    def get_author(obj):
        user = int(getattr(SocialAccount.objects.filter(user=obj.author).first(), 'uid', 0)) or obj.author.username \
            if obj.author else None
        return user

    @staticmethod
    def get_guild_id(obj):
        return int(obj.guild_id) if obj.guild_id else None

    class Meta:
        model = Log
        fields = ('author', 'short_code', 'log_type', 'guild_id', 'url', 'generated_at', 'expires_at')
