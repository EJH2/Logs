from datetime import datetime

import dateutil.parser
import pytz
import shortuuid
from django.contrib.postgres import fields
from django.db import models
from natural.date import duration
from natural.size import filesize

from django_logs.formatter import format_content_html, format_micro_content_html


class LogRoute(models.Model):
    url = models.TextField(editable=False, null=True)
    short_code = models.CharField(max_length=5, editable=False, unique=True)
    log_type = models.CharField(max_length=20, editable=False)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = fields.JSONField(editable=False)

    @classmethod
    def generate_short_code(cls, data):
        return shortuuid.uuid(str(data))[:5]

    def save(self, *args, **kwargs):
        if not self.id:
            self.short_code = self.generate_short_code(self.data)
        super(LogRoute, self).save(*args, **kwargs)

    def __str__(self):
        return 'Log %s' % self.short_code


class LogEntry:
    def __init__(self, data):
        self.generated_at = data['generated_at'] if data.get('generated_at', None) else None
        tz = self.generated_at.tzinfo if self.generated_at else pytz.UTC
        self.human_generated_at = duration(self.generated_at, now=datetime.now(tz=tz)) if self.generated_at else None
        self.messages = [Message(m) for m in self.sorted(data['messages'])]
        self.users = data['users']
        self.raw_content = data['raw_content']
        self.type = data['type']

    @classmethod
    def sorted(cls, messages: list):

        def sort_chronologcal(value):
            return int(value.get('message_id') or 0) or dateutil.parser.parse(value.get('timestamp'))

        messages.sort(key=sort_chronologcal)
        return messages

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
        self.id = int(data.get('id'))
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
        return other.id == self.id


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
            self.id = data.rsplit('/', 2)[1]
            self.filename = data.rsplit('/', 2)[2]
            self.url = data
            self.is_image = True
            self.size = 0
            self.error = False
        else:
            self.id = int(data['id'])
            self.filename = data['filename']
            self.url = data['url']
            self.is_image = data['is_image']
            self.size = filesize(data['size'])
            self.error = data['error']

    @classmethod
    def from_dict(cls, data: dict):
        self = cls.__new__(cls)

        for k in data:
            setattr(self, k, data[k])

        return self


class SerializedEmbed:
    def __init__(self, data):
        self.title = data.get('title', None)
        if self.title:
            self.title = format_micro_content_html(self.title)
        self.description = data.get('description', None)
        if self.description:
            self.description = format_content_html(self.description, masked_links=True)
        self.url = data.get('url', None)
        self.type = data.get('type', 'rich')
        self.author = data.get('author', None)
        self.timestamp = data.get('timestamp', None)
        self.color = f'#{data.get("color", 5198940):06X}'  # default discord embed color
        self.image = data.get('image', None)
        self.thumbnail = data.get('thumbnail', None)
        self.fields = data.get('fields', [])
        if len(self.fields) > 0:
            for field in self.fields:
                field['name'] = format_micro_content_html(field['name'])
                field['value'] = format_content_html(field['value'], masked_links=True)
        self.footer = data.get('footer', [])


class Embed:
    def __init__(self, data):
        self.title = data.get('title', None)
        self.description = data.get('description', None)
        self.url = data.get('url', None)
        self.type = data.get('type', 'rich')
        self.author = data.get('author', None)
        ts = data.get('timestamp', None)
        self.timestamp = ts if ts is None else dateutil.parser.parse(ts, default=datetime.now(tz=pytz.UTC))
        tz = self.timestamp.tzinfo if self.timestamp else pytz.UTC
        self.human_timestamp = duration(self.timestamp.replace(tzinfo=tz), now=datetime.now(tz=tz)) if \
            self.timestamp else None
        self.color = data.get("color", '#4F545C')
        self.image = data.get('image', None)
        self.thumbnail = data.get('thumbnail', None)
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
        self.timestamp = data.get('timestamp', None)
        self.raw_content = data['content']
        self.content = format_content_html(self.raw_content, masked_links=True)
        self.attachments = [Attachment(a).__dict__ for a in data['attachments']]
        self.embeds = [SerializedEmbed(e).__dict__ for e in data['embeds']]
        self.author = User(data['author']).__dict__
        self.edited = data.get('edited', False)


class Message:
    def __init__(self, data):
        self.id = int(data['id']) if data.get('id') else None
        ts = data.get('timestamp', None)
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
