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


class ChannelSerializer(BaseSerializer):
    id = serializers.IntegerField()
    guild_id = serializers.IntegerField()
    type = serializers.IntegerField()
    name = serializers.CharField()


class AttachmentSerializer(BaseSerializer):
    id = serializers.IntegerField()
    filename = serializers.CharField()
    size = serializers.IntegerField()
    url = serializers.URLField()
    proxy_url = serializers.URLField()
    height = serializers.IntegerField(allow_null=True)
    width = serializers.IntegerField(allow_null=True)


class EmbedFooterSerializer(BaseSerializer):
    text = serializers.CharField()
    icon_url = serializers.URLField(required=False)
    proxy_icon_url = serializers.URLField(required=False)


class EmbedImageSerializer(BaseSerializer):
    url = serializers.URLField(required=False)
    proxy_url = serializers.URLField(required=False)
    height = serializers.IntegerField(required=False)
    width = serializers.IntegerField(required=False)


class EmbedThumbnailSerializer(BaseSerializer):
    url = serializers.URLField(required=False)
    proxy_url = serializers.URLField(required=False)
    height = serializers.IntegerField(required=False)
    width = serializers.IntegerField(required=False)


class EmbedVideoSerializer(BaseSerializer):
    url = serializers.URLField(required=False)
    height = serializers.IntegerField(required=False)
    width = serializers.IntegerField(required=False)


class EmbedProviderSerializer(BaseSerializer):
    name = serializers.CharField(required=False)
    url = serializers.URLField(required=False)


class EmbedAuthorSerializer(BaseSerializer):
    name = serializers.CharField(required=False)
    url = serializers.URLField(required=False)
    icon_url = serializers.URLField(required=False)
    proxy_icon_url = serializers.URLField(required=False)


class EmbedFieldSerializer(BaseSerializer):
    name = serializers.CharField()
    value = serializers.CharField()
    inline = serializers.BooleanField(required=False)


class EmbedSerializer(BaseSerializer):
    title = serializers.CharField(required=False)
    type = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    url = serializers.URLField(required=False)
    timestamp = serializers.DateTimeField(required=False)
    color = serializers.IntegerField(required=False)
    footer = EmbedFooterSerializer(required=False)
    image = EmbedImageSerializer(required=False)
    thumbnail = EmbedThumbnailSerializer(required=False)
    video = EmbedVideoSerializer(required=False)
    provider = EmbedProviderSerializer(required=False)
    author = EmbedAuthorSerializer(required=False)
    fields = EmbedFieldSerializer(required=False, many=True)


class EmojiSerializer(BaseSerializer):
    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField(allow_null=True)
    roles = RoleSerializer(many=True, required=False)
    user = UserSerializer(required=False)
    require_colons = serializers.BooleanField(required=False)
    managed = serializers.BooleanField(required=False)
    animated = serializers.BooleanField(required=False)
    available = serializers.BooleanField(required=False)


class ReactionSerializer(BaseSerializer):
    count = serializers.IntegerField()
    me = serializers.BooleanField()
    emoji = EmojiSerializer()
