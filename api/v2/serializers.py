import json

import requests
from rest_framework import serializers

from api import utils
from api.consts import privacy_types
from api.models import Log
from api.utils import get_default_timestamp


class LogCreateSerializer(serializers.Serializer):
    type = serializers.CharField(help_text='Log type.')
    messages = serializers.JSONField(help_text='Array of Discord message objects.')
    expires = serializers.DateTimeField(allow_null=True, default=get_default_timestamp,
                                        help_text='Log expiration in UTC.')
    privacy = serializers.CharField(default='public', help_text='Log privacy.')
    guild = serializers.IntegerField(allow_null=True, default=None,
                                     help_text='Linked guild of log. Must be set if privacy '
                                               'setting is either guild or mods.')

    @staticmethod
    def validate_messages(value):
        """Check if messages are a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError('Messages must be a valid JSON array of Discord message objects!')
        return value

    def validate_expires(self, value):
        """Check if expiry time is within parameters"""
        return utils.validate_expires(self.context['user'], value)

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
        if ret['privacy'] in ['public', 'invite']:
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

    def validate_expires(self, value):
        """Check if expiry time is within parameters"""
        return utils.validate_expires(self.context['user'], value)

    @staticmethod
    def validate_privacy(value):
        """Check if privacy value is within parameters"""
        if value not in privacy_types:
            raise serializers.ValidationError(f'Privacy value must be one of {", ".join(privacy_types)}!')
        return value

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


class LogArchiveCreateSerializer(serializers.Serializer):
    type = serializers.CharField(help_text='Log type.')
    url = serializers.URLField(help_text='URL containing valid JSON array of Discord message objects.')
    expires = serializers.DateTimeField(allow_null=True, default=get_default_timestamp,
                                        help_text='Log expiration in UTC.')
    privacy = serializers.CharField(default='public', help_text='Log privacy.')
    guild = serializers.IntegerField(allow_null=True, default=None,
                                     help_text='Linked guild of log. Must be set if privacy '
                                               'setting is either guild or mods.')

    @staticmethod
    def validate_url(value):
        """Check if url content is a valid list"""
        if not isinstance(json.loads(requests.get(value).text), list):
            raise serializers.ValidationError('URL must lead to a valid JSON array of Discord message objects!')
        return value

    def validate_expires(self, value):
        """Check if expiry time is within parameters"""
        return utils.validate_expires(self.context['user'], value)

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
        if ret['privacy'] in ['public', 'invite']:
            ret['guild'] = None
        return ret

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class LogArchiveSerializer(serializers.Serializer):
    url = serializers.URLField(help_text='Archive URL.')

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
