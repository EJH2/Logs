from natural.size import filesize
from rest_framework import serializers

from api.formatter import to_html


def sort_null(_ret):
    ret = _ret.copy()
    for key in _ret:
        if _ret[key] is None:
            del ret[key]
    return ret


def mention_sub(match, mentions):
    m = next((item for item in mentions if str(item["id"]) == match.group(1)), None)
    return f'<@{m["username"]}#{m["discriminator"]} ({m["id"]})>'


def scale_image(height, width, max_height, max_width):
    if min(height,  width) == 0:
        return min(height, max_height), min(width, max_width)
    old_width = width
    width = old_width if old_width < max_width else max_width
    height = height / (old_width / width)
    if height > max_height:
        old_height = height
        height = max_height
        width = width / (old_height / max_height)
    return int(height), int(width)


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(min_length=2, max_length=32)
    discriminator = serializers.CharField(min_length=4, max_length=4)
    avatar = serializers.CharField(default=None, allow_null=True)
    bot = serializers.BooleanField(default=False)
    color = serializers.IntegerField(default=None)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get('color'):
            ret['color'] = f'#{ret["color"]:06X}'
        if not ret.get('avatar'):
            ret['avatar'] = f'https://cdn.discordapp.com/embed/avatars/{int(ret["discriminator"]) % 5}.png'
        else:
            ending = 'gif' if ret['avatar'].startswith('a_') else 'png'
            ret['avatar'] = f'https://cdn.discordapp.com/avatars/{ret["id"]}/{ret["avatar"]}.{ending}'
        return ret

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class AttachmentSerializer(serializers.Serializer):
    id = serializers.IntegerField(default=None)
    filename = serializers.CharField()
    url = serializers.CharField()
    proxy_url = serializers.CharField(default=None, allow_null=True)
    size = serializers.IntegerField(default=0)
    width = serializers.IntegerField(default=None, allow_null=True)
    height = serializers.IntegerField(default=None, allow_null=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['type'] = 'file'
        if ret.get('height') is not None or ret.get('width') is not None:
            ext = ret.get('filename').rsplit('.', 1)[-1]
            if ext in ['png', 'jpg', 'jpeg']:
                ret['type'] = 'image'
            elif ext in 'gifv':
                ret['type'] = 'gif'
            else:
                ret['type'] = 'video'
            ret['height'], ret['width'] = scale_image(ret['height'], ret['width'], 300, 400)
        ret['size'] = filesize(ret['size'])
        return ret

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ImageSerializer(serializers.Serializer):
    url = serializers.URLField()
    proxy_url = serializers.URLField(default=None, allow_null=True)
    width = serializers.IntegerField(default=None, allow_null=True)
    height = serializers.IntegerField(default=None, allow_null=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get('width') is not None:
            ret['height'], ret['width'] = scale_image(ret['height'], ret['width'], 300, 400)

        return sort_null(ret)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class EmbedAuthorSerializer(serializers.Serializer):
    name = serializers.CharField(default=None, allow_null=True)
    url = serializers.URLField(default=None, allow_null=True)
    icon_url = serializers.URLField(default=None, allow_null=True)
    proxy_icon_url = serializers.URLField(default=None, allow_null=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return sort_null(ret)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class EmbedProviderSerializer(serializers.Serializer):
    name = serializers.CharField(default=None, allow_null=True)
    url = serializers.URLField(default=None, allow_null=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return sort_null(ret)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class EmbedFieldSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256)
    value = serializers.CharField(max_length=2048)
    inline = serializers.BooleanField(default=False)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['name'] = to_html(ret['name'], options={'embed': 'lite', 'users': self.context['users']})
        ret['value'] = to_html(ret['value'], options={'embed': True, 'users': self.context['users']})
        return ret

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class EmbedFooterSerializer(serializers.Serializer):
    text = serializers.CharField(default=None, allow_null=True)
    icon_url = serializers.URLField(default=None, allow_null=True)
    proxy_icon_url = serializers.URLField(default=None, allow_null=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return sort_null(ret)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class EmbedSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=256, default=None, allow_null=True)
    description = serializers.CharField(max_length=2048, default=None, allow_null=True)
    url = serializers.URLField(default=None, allow_null=True)
    type = serializers.CharField(max_length=20, default='rich')
    timestamp = serializers.DateTimeField(default=None, allow_null=True)
    color = serializers.IntegerField(default=None, allow_null=True)
    image = ImageSerializer(default=None, allow_null=True)
    thumbnail = ImageSerializer(default=None, allow_null=True)
    video = ImageSerializer(default=None, allow_null=True)
    author = EmbedAuthorSerializer(default=None, allow_null=True)
    provider = EmbedProviderSerializer(default=None, allow_null=True)
    fields = EmbedFieldSerializer(many=True, default=[], allow_null=True)
    footer = EmbedFooterSerializer(required=False, default={}, allow_null=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get('title'):
            ret['title'] = to_html(ret['title'], options={'embed': 'lite', 'users': self.context['users']})
        if ret.get('description'):
            ret['description'] = to_html(ret['description'], options={'embed': True, 'users': self.context['users']})
        ret['color'] = f'#{ret["color"]:06X}' if ret.get('color') else None

        if ret['type'] == 'article' and not (ret.get('title') or ret.get('description')):
            ret['type'] = 'image'

        ret['thumbnail'] = ret.get('thumbnail') or {}
        if ret['thumbnail'].get('width') and ret['type'] in ['link', 'rich'] or ret['image']:
            img = 'thumbnail' if ret['thumbnail'] else 'image'
            ret['thumbnail']['height'], ret['thumbnail']['width'] = scale_image(
                ret[img]['height'], ret[img]['width'], 80, 80
            )

        return ret

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class MessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(default=None)
    channel_id = serializers.IntegerField(default=None)
    guild_id = serializers.IntegerField(default=None)
    author = AuthorSerializer()
    mentions = AuthorSerializer(many=True, default=[])
    timestamp = serializers.DateTimeField(default=None)
    edited_timestamp = serializers.DateTimeField(default=None, allow_null=True)
    content = serializers.CharField(default='', allow_blank=True)
    attachments = AttachmentSerializer(many=True, default=[])
    embeds = EmbedSerializer(many=True, default=[])

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['_content'] = ret['content']
        webhook_mode = True if ret['author'].get('bot') and ret['author'].get('discriminator') == '0000' else False
        ret['content'] = to_html(ret['content'], options={'embed': webhook_mode, 'users': self.context['users']})
        return ret

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
