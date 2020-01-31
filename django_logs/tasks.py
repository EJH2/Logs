import re
from datetime import datetime, timedelta

import dateutil.parser
import pytz
# import requests
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.core import serializers

from django_logs import handlers, utils
# from django_logs.consts import DISCORD_API_URL, DISCORD_HEADERS, DISCORD_TOKEN
from django_logs.consts import types
from django_logs.models import SerializedMessage, User, Job
from django_logs.utils import create_log_entry


@shared_task(bind=True)
def parse(self, create_data: dict):
    """
    Convert raw log content into usable data.
    :param self: Task instance, supplied by Celery.
    :param create_data: Default log parameters.
    :return: Parsed data.
    """
    log_type = create_data['log_type']
    parser = getattr(handlers, log_type)
    content = create_data['content']
    match_data = parser(content, ProgressRecorder(self))
    return match_data


@shared_task(bind=True)
def parse_messages(self, match_data: dict):
    """
    Convert parsed data into formatted data.
    :param self: Task instance, supplied by Celery.
    :param match_data: Parsed data.
    :return: Formatted data.
    """
    users = list()
    _users = dict()
    _messages = list()
    messages = list()
    data = dict()

    total = len(match_data)
    progress = ProgressRecorder(self)

    for count, match in enumerate(match_data):
        uid = match.get('uid')
        message_dict = {'id': match.get('mid'), 'timestamp': match.get('time'), 'content': match['content']}

        user = {'id': uid, 'username': match.get('uname') or 'Unknown User',
                'discriminator': match.get('disc') or '0000', 'avatar': match.get('avatar')}

        if not uid:
            uid = f'{user["username"]}#{user["discriminator"]}'

        def get_default():
            return f'https://cdn.discordapp.com/embed/avatars/{int(user["discriminator"]) % 5}.png'

        if uid not in _users:
            user['avatar'] = user['avatar'] or get_default()
            _users[uid] = user
            users.append(User(user).__dict__)
        else:
            user = _users[uid]
        message_dict['author'] = user

        message_dict['attachments'] = []
        if match.get('attach', []):
            if len(match['attach']) > 0 and match['attach'][0] != '':
                message_dict['attachments'] = match['attach'] if isinstance(match['attach'], list) else \
                    [match['attach']]

        message_dict['embeds'] = []
        if match.get('embeds', []):
            if len(match['embeds']) > 0 and match['embeds'][0] != '':
                message_dict['embeds'] = match['embeds']

        _messages.append(message_dict)

        progress.set_progress(count + 1, total)

    for msg in _messages:
        messages.append(SerializedMessage(msg, _users).__dict__)

    def sort_chronological(value):
        return int(value.get('id') or 0) or dateutil.parser.parse(value.get('timestamp'))

    if any([messages[0].get('timestamp'), messages[0].get('id')]):
        messages.sort(key=sort_chronological)
    data['messages'] = messages

    def sort_alphabetical(value):
        return value['username']

    users.sort(key=sort_alphabetical)
    data['users'] = users

    return data


@shared_task(bind=True)
def create_log(self, data: dict, create_data: dict):
    """
    Take formatted data and save it to a log.
    :param self: Task instance, supplied by Celery.
    :param data: Formatted data.
    :param create_data: Default log parameters.
    :return: Log short code.
    """
    progress = ProgressRecorder(self)

    variant = create_data.pop('variant')
    create_data['log_type'] = variant[0] if variant else create_data['log_type']
    data['type'] = variant[1] if variant else types[create_data['log_type']]

    messages = data.pop('messages')
    create_data['data'] = data
    if create_data['author']:
        create_data['author'] = list(serializers.deserialize('json', create_data['author']))[0].object

    expires = create_data.pop('expires')
    create_data['expires_at'] = datetime.now(tz=pytz.UTC) + timedelta(seconds=expires) if expires else expires

    progress.set_progress(1, 2)
    created_log = create_log_entry(**create_data, messages=messages)
    progress.set_progress(2, 2)

    job = Job.objects.filter(short_code=created_log.short_code)
    utils.forget_tasks(job)

    return created_log.short_code


# JSON parsing task
@shared_task(bind=True)
def parse_json(self, json_data: dict):
    """
    Convert raw JSON into finished message objects.
    :param self: Task instance, supplied by Celery.
    :param json_data: Raw JSON.
    :return: Parsed data.
    """
    users = list()
    messages = list()
    data = dict()

    total = len(json_data)
    progress = ProgressRecorder(self)

    for count, msg in enumerate(json_data):
        author = msg.get('author', {'id': 0, 'username': 'Unknown User', 'discriminator': '0000'})

        if not author.get('avatar'):
            author['avatar'] = f'https://cdn.discordapp.com/embed/avatars/{int(author["discriminator"]) % 5}.png'
        if re.match(r'(?:a_)?[a-zA-Z0-9]{32}', author.get('avatar')):
            ending = 'gif' if author['avatar'].startswith('a_') else 'png'
            author['avatar'] = f'https://cdn.discordapp.com/avatars/{author["id"]}/{author["avatar"]}.{ending}'
        if author not in users:
            users.append(author)

        if msg.get('mentions'):
            for m in msg['mentions']:
                msg['content'] = re.sub(rf'<@!?{m["id"]}>', f'<@{m["username"]}#{m["discriminator"]} ({m["id"]})>',
                                        msg['content'])

        if msg.get('attachments'):
            for a in msg['attachments']:
                a['is_image'] = False
                if any([a.get('height'), a.get('width'),
                        a['filename'].rsplit('.', 1)[-1] in ['png', 'jpg', 'jpeg', 'gif', 'webm', 'webp', 'mp4']]):
                    a['is_image'] = True
                    continue
                if re.match(r'data:(?:image/(?P<mimetype>\w+))?(?:;(?P<b64>base64))?,(?P<data>(?:[A-Za-z0-9+/]{4})'
                            r'``*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?)', a['url']):
                    a['is_image'] = True

        messages.append(SerializedMessage(msg).__dict__)

        progress.set_progress(count, total)

    def sort_chronological(value):
        return int(value.get('id') or 0) or dateutil.parser.parse(value.get('timestamp'))

    if any([messages[0].get('timestamp'), messages[0].get('id')]):
        messages.sort(key=sort_chronological)
    data['messages'] = messages

    def sort_alphabetical(value):
        return value['username']

    users.sort(key=sort_alphabetical)
    data['users'] = users

    return data


@shared_task(bind=True)
def create_json_log(self, data: dict, create_data: dict):
    """
    Take formatted JSON log data and save it to a log.
    :param self: Task instance, supplied by Celery.
    :param data: Formatted data.
    :param create_data: Default log parameters.
    :return: Log short code.
    """
    progress = ProgressRecorder(self)

    data['type'] = types[create_data['log_type']] if create_data.get('log_type') else None

    messages = data.pop('messages')
    create_data['data'] = data
    if create_data['author']:
        create_data['author'] = list(serializers.deserialize('json', create_data['author']))[0].object

    expires = create_data.pop('expires')
    create_data['expires_at'] = datetime.now(tz=pytz.UTC) + timedelta(seconds=expires) if expires else expires

    progress.set_progress(1, 2)
    created_log = create_log_entry(**create_data, messages=messages)
    progress.set_progress(2, 2)

    job = Job.objects.filter(short_code=created_log.short_code)
    utils.forget_tasks(job)

    return created_log.short_code
