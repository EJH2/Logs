import requests
from rest_framework import serializers

from api.consts import expiry_times, form_types, privacy_types
from api.models import Log
from api.utils import validate_expires


class LogCreateSerializer(serializers.Serializer):
    type = serializers.CharField(help_text='Log type.')
    url = serializers.URLField(help_text='URL containing messages.')
    expires = serializers.CharField(allow_null=True, default='30min', help_text='Log expiration.')
    privacy = serializers.CharField(default='public', help_text='Log privacy.')
    guild = serializers.IntegerField(allow_null=True, help_text='Linked guild of log.')

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
        if not requests.head(value).headers['content-type'] == 'text/plain':
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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['expires'] = expiry_times[ret['expires']]
        ret['messages'] = requests.get(ret.pop('url')).text
        if ret['privacy'] in ['public', 'invite']:
            ret['guild'] = None
        return ret


class LogErrorSerializer(serializers.Serializer):
    errors = serializers.JSONField(help_text='Request errors.')


class LogListSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username', help_text='Log\'s owner.')
    url = serializers.HyperlinkedIdentityField(view_name='log-html', help_text='Log\'s URL.')

    class Meta:
        model = Log
        fields = ('owner', 'uuid', 'url', 'type', 'created', 'expires')
