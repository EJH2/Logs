from rest_framework import serializers

from django_logs.models import Log


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ('author', 'short_code', 'log_type', 'url', 'generated_at', 'expires_at')
