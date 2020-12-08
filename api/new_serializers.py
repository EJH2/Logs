from rest_framework import serializers


class BaseSerializer(serializers.Serializer):

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class UserSerializer(BaseSerializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    discriminator = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)
    bot = serializers.BooleanField(required=False)
    system = serializers.BooleanField(required=False)
    mfa_enabled = serializers.BooleanField(required=False)
    locale = serializers.CharField(required=False)
    verified = serializers.BooleanField(required=False)
    email = serializers.CharField(required=False, allow_null=True)
    flags = serializers.IntegerField(required=False)
    premium_type = serializers.IntegerField(required=False)
    public_flags = serializers.IntegerField(required=False)


class MemberSerializer(BaseSerializer):
    user = UserSerializer(required=False)
    nick = serializers.CharField(allow_null=True)
    roles = serializers.ListSerializer(child=serializers.IntegerField())
    joined_at = serializers.DateTimeField()
    premium_since = serializers.DateTimeField(required=False, allow_null=True)
    deaf = serializers.BooleanField()
    mute = serializers.BooleanField()


class RoleSerializer(BaseSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.IntegerField()
    hoist = serializers.BooleanField()
    position = serializers.IntegerField()
    permissions = serializers.CharField()
    managed = serializers.BooleanField()
    mentionable = serializers.BooleanField()
