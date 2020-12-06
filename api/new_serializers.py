from rest_framework import serializers


class BaseSerializer(serializers.Serializer):

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class UserSerializer(BaseSerializer):
    id = serializers.IntegerField()
    username = serializers.CharField(min_length=2, max_length=32)
    discriminator = serializers.CharField(min_length=4, max_length=4)
    avatar = serializers.CharField(allow_null=True)
    bot = serializers.BooleanField(required=False, default=False)
    system = serializers.BooleanField(required=False, default=False)
    mfa_enabled = serializers.BooleanField(required=False)
    locale = serializers.CharField(required=False)
    verified = serializers.BooleanField(required=False)
    email = serializers.CharField(required=False, allow_null=True)
    flags = serializers.IntegerField(required=False)
    premium_type = serializers.IntegerField(required=False)
    public_flags = serializers.IntegerField(required=False)

