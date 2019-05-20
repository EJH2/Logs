from datetime import datetime

import dateutil.parser
import pytz
import shortuuid
from django.contrib.auth.models import User as DjangoUser
from django.contrib.postgres import fields
from django.db import models
from natural.date import duration
from natural.size import filesize

from django_logs.formatter import format_content_html, format_micro_content_html


class LogRoute(models.Model):
    author = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, null=True)
    origin = models.CharField(max_length=10)
    url = models.TextField(null=True)
    short_code = models.CharField(max_length=15, editable=False, unique=True)
    log_type = models.CharField(max_length=30)
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True)
    data = fields.JSONField(null=True)
    content = models.TextField(null=True)
    messages = fields.JSONField()
    chunked = models.BooleanField(default=False)

    @classmethod
    def generate_short_code(cls, data):
        return shortuuid.uuid(str(data))[:5]

    def __str__(self):
        return 'Log %s' % self.short_code


class ActiveJob(models.Model):
    short_code = models.CharField(max_length=15, editable=False, unique=True)
    data = fields.JSONField()
    request_uri = models.TextField(null=True)


class LogEntry:
    def __init__(self, data):
        self.generated_at = data['generated_at'] if data.get('generated_at') else None
        tz = self.generated_at.tzinfo if self.generated_at else pytz.UTC
        self.human_generated_at = duration(self.generated_at, now=datetime.now(tz=tz)) if self.generated_at else None
        self.messages = [Message(m) for m in data['messages']]
        self.users = data['users']
        self.ids = list(u['id'] for u in self.users if u['id'])
        self.raw_content = data['raw_content']
        self.type = data['type']

    @property
    def message_groups(self):
        groups = []

        if not self.messages:
            return groups

        curr = MessageGroup(self.messages[0].author)

        for index, message in enumerate(self.messages):
            next_index = index + 1 if index + 1 < len(self.messages) else index
            next_message = self.messages[next_index]

            curr.messages.append(message)

            if message.is_different_from(next_message):
                groups.append(curr)
                curr = MessageGroup(next_message.author)

        groups.append(curr)
        return groups


class User:
    def __init__(self, data):
        self.id = int(data['id']) if data.get('id') else None
        self.name = data['username']
        self.discriminator = data['discriminator']
        self.avatar_url = data['avatar']
        self.bot = data.get('bot', False)

    @property
    def default_avatar_url(self):
        return "https://cdn.discordapp.com/embed/avatars/{}.png".format(
            int(self.discriminator) % 5
        )

    @classmethod
    def from_dict(cls, data: dict):
        self = cls.__new__(cls)

        for k in data:
            setattr(self, k, data[k])

        return self

    def __str__(self):
        return f'{self.name}#{self.discriminator}'

    def __eq__(self, other):
        return other.__dict__ == self.__dict__


class MessageGroup:
    def __init__(self, author):
        self.author = author
        self.messages = []

    @property
    def created_at(self):
        return self.messages[0].created_iso

    @property
    def human_created_at(self):
        return self.messages[0].human_created_at

    @property
    def type(self):
        return self.messages[0].type


class Attachment:
    def __init__(self, data):
        if isinstance(data, str):  # Backwards compatibility
            self.filename = data.rsplit('/', 1)[1]
            self.url = data
            self.is_image = True
            self.size = 0
        else:
            self.filename = data['filename']
            self.url = data['url']
            self.is_image = data['is_image']
            self.size = filesize(data['size'])

    @classmethod
    def from_dict(cls, data: dict):
        self = cls.__new__(cls)

        for k in data:
            setattr(self, k, data[k])

        return self


class SerializedEmbed:
    def __init__(self, data):
        self.title = data.get('title')
        if self.title:
            self.title = format_micro_content_html(self.title)
        self.description = data.get('description')
        if self.description:
            self.description = format_content_html(self.description, masked_links=True, newlines=False)
        self.url = data.get('url')
        self.type = data.get('type', 'rich')
        self.author = data.get('author')
        self.timestamp = data.get('timestamp')
        self.color = f'#{data.get("color", 5198940):06X}'  # default discord embed color
        self.image = data.get('image')
        self.thumbnail = data.get('thumbnail')
        self.fields = data.get('fields', [])
        if len(self.fields) > 0:
            for field in self.fields:
                field['name'] = format_micro_content_html(field['name'])
                field['value'] = format_content_html(field['value'], masked_links=True)
        self.footer = data.get('footer', [])


class Embed:
    def __init__(self, data):
        self.title = data.get('title')
        self.description = data.get('description')
        self.url = data.get('url')
        self.type = data.get('type', 'rich')
        self.author = data.get('author')
        ts = data.get('timestamp')
        self.timestamp = dateutil.parser.parse(ts, default=datetime.now(tz=pytz.UTC)) if ts else ts
        self.t = type(self.timestamp)
        tz = self.timestamp.tzinfo if self.timestamp else pytz.UTC
        self.human_timestamp = duration(self.timestamp.replace(tzinfo=tz), now=datetime.now(tz=tz)) if \
            self.timestamp else None
        self.color = data.get("color", '#4F545C')
        self.image = data.get('image')
        self.thumbnail = data.get('thumbnail')
        self.fields = data.get('fields', [])
        self.footer = data.get('footer', [])

    @classmethod
    def from_dict(cls, data: dict):
        self = cls.__new__(cls)

        for k in data:
            setattr(self, k, data[k])

        return self


class SerializedMessage:
    def __init__(self, data):
        self.id = int(data['message_id']) if data.get('message_id') else None
        self.timestamp = data.get('timestamp')
        self.raw_content = data['content']
        self.content = format_content_html(self.raw_content, masked_links=True)
        self.attachments = [Attachment(a).__dict__ for a in data['attachments']]
        self.embeds = [SerializedEmbed(e).__dict__ for e in data['embeds']]
        self.author = User(data['author']).__dict__
        self.edited = data.get('edited', False)


class Message:
    def __init__(self, data):
        self.id = int(data['id']) if data.get('id') else None
        ts = data.get('timestamp')
        self.created_at = dateutil.parser.parse(ts, default=datetime.now(tz=pytz.UTC)) if ts else None
        self.created_iso = self.created_at.isoformat() if ts else None
        tz = self.created_at.tzinfo if self.created_at else pytz.UTC
        self.human_created_at = duration(self.created_at.replace(tzinfo=tz), now=datetime.now(tz=tz)) if \
            self.created_at else None
        self.raw_content = data['raw_content']
        self.content = data['content']
        self.attachments = [Attachment.from_dict(a) for a in data['attachments']]
        self.embeds = [Embed.from_dict(e) for e in data['embeds']]
        self.author = User.from_dict(data['author'])
        self.edited = data.get('edited', False)

        # Check to see if the message has any content, and if not, make the message an error
        self.error = ''
        if not any([self.raw_content, self.attachments, self.embeds]):  # No content, attachments or embeds
            self.error = 'error'
            self.content = '[No Message Content]'

    def is_different_from(self, other):
        if self.created_at is not None:
            return (
                    (other.created_at - self.created_at).total_seconds() > 60
                    or other.author != self.author
            )
        return other.author != self.author


# class User(models.Model):
#     id = models.BigIntegerField(null=True)
#     name = models.CharField(max_length=100)
#     discriminator = models.CharField(max_length=4)
#     avatar_url = models.TextField(null=True)
#     bot = models.BooleanField(default=False)
#
#     @property
#     def default_avatar_url(self):
#         return "https://cdn.discordapp.com/embed/avatars/{}.png".format(
#             int(self.discriminator) % 5
#         )
#
#     def __str__(self):
#         return f'{self.name}#{self.discriminator}'
#
#     def __eq__(self, other):
#         return other.__dict__ == self.__dict__
#
#
# class EmbedField(models.Model):
#     name = models.CharField(max_length=256)
#     value = models.CharField(max_length=1024)
#     inline = models.BooleanField()
#
#
# class EmbedAuthor(models.Field):
#     name = models.CharField()
#     url = models.CharField(null=True)
#     icon_url = models.CharField(null=True)
#
#
# class EmbedFooter(models.Model):
#     text = models.CharField(max_length=2048, null=True)
#     icon_url = models.TextField(null=True)
#
#
# class Embed(models.Model):
#     title = models.CharField(max_length=256, null=True)
#     description = models.CharField(max_length=2048, null=True)
#     type = models.CharField(max_length=25, default='rich')
#     url = models.TextField(null=True)
#     author = pgfields.JSONField(null=True)
#     timestamp = models.DateTimeField(null=True)
#     color = models.IntegerField(default=5198940)
#     fields = pgfields.ArrayField(pgfields.JSONField(null=True), size=25)
#     thumbnail = pgfields.JSONField(null=True)
#     image = pgfields.JSONField(null=True)
#     footer = pgfields.JSONField(null=True)
#
#
# class Attachment(models.Model):
#     filename = models.TextField()
#     url = models.TextField()
#     is_image = models.BooleanField()
#     size = models.CharField(max_length=25)
#
#
# class Message(models.Model):
#     id = models.BigIntegerField(null=True)
#     type = models.CharField(max_length=4, default='raw')
#     author = models.ForeignKey(User, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(null=True)
#     content = models.TextField(null=True)
#     attachments = models.ManyToManyField(Attachment)
#     embeds = models.ManyToManyField(Embed)
#
#     def is_different_from(self, other):
#         if self.created_at is not None:
#             return (
#                     (other.created_at - self.created_at).total_seconds() > 60
#                     or other.author != self.author
#             )
#         return other.author != self.author
#
#     @property
#     def created_iso(self):
#         return self.created_at.isoformat() if self.created_at else None
#
#     @property
#     def human_created_at(self):
#         tz = self.created_at.tzinfo if self.created_at else pytz.UTC
#         return duration(self.created_at.replace(tzinfo=tz), now=datetime.now(tz=tz)) if self.created_at else None
#
#     def save(self, *args, **kwargs):
#         if self.type == 'raw':
#             self.content = format_content_html(self.content, masked_links=True)
#             self.type = 'rich'
#         super(Message, self).save(*args, **kwargs)
