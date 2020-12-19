import requests
from api import utils
from rest_framework import serializers

from api.consts import form_types, privacy_types
from api.models import Log
from api.utils import validate_expires, get_default_timestamp


class LogCreateSerializer(serializers.Serializer):
    type = serializers.CharField(help_text='Log type.')
    url = serializers.URLField(help_text='URL containing messages.')
    expires = serializers.DateTimeField(allow_null=True, default=get_default_timestamp,
                                        help_text='Log expiration in UTC.')
    privacy = serializers.CharField(default='public', help_text='Log privacy.')
    guild = serializers.IntegerField(allow_null=True, default=None,
                                     help_text='Linked guild of log. Must be set if privacy '
                                               'setting is either guild or mods.')

    @staticmethod
    def validate_type(value):
        """Check if log type is something we know how to parse, and if not, return an error"""
        if value not in form_types:
            raise serializers.ValidationError(f'Log type must be one of {", ".join(form_types.keys())}! If you want'
                                              f'to see your format added, join the Discord at '
                                              f'https://discord.gg/3X8WwbU')
        return value

    @staticmethod
    def validate_url(value):
        """Check if url content type is text/plain"""
        if 'text/plain' not in requests.head(value).headers['content-type']:
            raise serializers.ValidationError('URL Content-Type must be text/plain!')
        return value

    def validate_expires(self, value):
        """Check if expiry time is within parameters"""
        return validate_expires(self.context['user'], value)

    @staticmethod
    def validate_privacy(value):
        """Check if privacy value is within parameters"""
        if value not in privacy_types:
            raise serializers.ValidationError(f'Privacy value must be one of {", ".join(privacy_types)}!')
        return value

    def validate_guild(self, value):
        """Check to see if there is a guild if the privacy type requires one"""
        if self.initial_data.get('privacy', 'public') in ['guild', 'mods'] and not value:
            raise serializers.ValidationError('A guild must be set if the privacy type is set to guild, mods!')
        return value

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['messages'] = requests.get(ret.pop('url')).text
        if ret['privacy'] == 'public':
            ret['guild'] = None
        return ret

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class LogPatchSerializer(serializers.Serializer):
    expires = serializers.DateTimeField(required=False, help_text='Log expiration in UTC.')
    privacy = serializers.CharField(required=False, help_text='Log privacy.')
    guild = serializers.IntegerField(allow_null=True, required=False,
                                     help_text='Linked guild of log. Must be set if privacy '
                                               'setting is either guild or mods.')

    @staticmethod
    def validate_privacy(value):
        """Check if privacy value is within parameters"""
        if value not in privacy_types:
            raise serializers.ValidationError(f'Privacy value must be one of {", ".join(privacy_types)}!')
        return value

    def validate_expires(self, value):
        """Check if expiry time is within parameters"""
        return utils.validate_expires(self.context['user'], value)

    def validate_guild(self, value):
        """Check to see if there is still a guild if the privacy type requires one"""
        if self.initial_data.get('privacy', 'public') in ['guild', 'mods'] and not value:
            raise serializers.ValidationError('A guild must be set if the privacy type is set to guild, mods!')
        return value

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class LogErrorSerializer(serializers.Serializer):
    errors = serializers.JSONField(help_text='Request errors.')

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class LogListSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username', help_text='Log\'s owner.')
    url = serializers.HyperlinkedIdentityField(view_name='log-html', help_text='Log\'s URL.')

    class Meta:
        model = Log
        fields = ('owner', 'uuid', 'url', 'type', 'created', 'expires', 'privacy', 'guild')
