import json

import requests
from rest_framework import serializers

from api import utils
from api.consts import expiry_times, privacy_types
from api.models import Log


class LogCreateSerializer(serializers.Serializer):
    type = serializers.CharField(help_text='Log type.')
    messages = serializers.JSONField(help_text='Array of Discord message objects.')
    expires = serializers.CharField(allow_null=True, default='30min', help_text='Log expiration.')
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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['expires'] = expiry_times[ret['expires']]
        if ret['privacy'] in ['public', 'invite']:
            ret['guild'] = None
        return ret


class LogErrorSerializer(serializers.Serializer):
    errors = serializers.JSONField(help_text='Request errors.')


class LogArchiveCreateSerializer(serializers.Serializer):
    type = serializers.CharField(help_text='Log type.')
    url = serializers.URLField(help_text='URL containing valid JSON array of Discord message objects.')
    expires = serializers.CharField(allow_null=True, default='30min', help_text='Log expiration.')
    privacy = serializers.CharField(default='public', help_text='Log privacy.')
    guild = serializers.IntegerField(allow_null=True, default=None, help_text='Linked guild of log. Must be set if privacy setting is either guild or mods.')

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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['expires'] = expiry_times[ret['expires']]
        if ret['privacy'] in ['public', 'invite']:
            ret['guild'] = None
        return ret


class LogArchiveSerializer(serializers.Serializer):
    url = serializers.URLField(help_text='Archive URL.')


class LogListSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username', help_text='Log\'s owner.')
    url = serializers.HyperlinkedIdentityField(view_name='log-html', help_text='Log\'s URL.')

    class Meta:
        model = Log
        fields = ('owner', 'uuid', 'url', 'type', 'created', 'expires')
