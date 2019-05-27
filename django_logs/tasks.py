from datetime import datetime, timedelta

import dateutil.parser
import pytz
# import requests
from celery import shared_task
from celery_progress.backend import ProgressRecorder

from django.core import serializers

from django_logs import handlers
# from django_logs.consts import DISCORD_API_URL, DISCORD_HEADERS, DISCORD_TOKEN
from django_logs.models import SerializedMessage, User
from django_logs.utils import create_log_entry


@shared_task(bind=True)
def parse(self, create_data):
    kwargs = {'pr': ProgressRecorder(self)}
    log_type = create_data['log_type']
    parser = getattr(handlers, log_type)
    content = create_data['content']
    variant = create_data.pop('variant')
    kwargs['variant'] = variant if variant else None
    data, data['match_data'] = parser(content, **kwargs)
    return data


@shared_task(bind=True)
def parse_messages(self, data: dict):
    users = list()
    _users = dict()
    messages = list()

    match_data = data.pop('match_data')

    total = len(match_data)
    progress_recorder = ProgressRecorder(self)

    for count, match in enumerate(match_data):
        uid = match.get('uid')
        message_dict = {'message_id': match.get('mid'), 'timestamp': match['time'],
                        'content': match['content']}

        user = {'id': uid, 'username': match.get('uname') or 'Unknown User',
                'discriminator': match.get('disc') or '0000', 'avatar': match.get('avatar')}

        if not uid:
            uid = f'{user["username"]}#{user["discriminator"]}'

        def get_avatar(default_avatar: bool = False):
            if default_avatar:
                return f'https://cdn.discordapp.com/embed/avatars/{int(user["discriminator"]) % 5}.png'
            if match.get('asset'):
                return f'https://discordapp.com/assets/{user["avatar"]}.png'
            ending = 'gif' if user['avatar'].startswith('a_') else 'png'
            return f'https://cdn.discordapp.com/avatars/{uid}/{user["avatar"]}.{ending}'

        if uid not in _users:
            if user.get('avatar'):  # User supplied avatar, don't bombard Discord's API
                user['avatar'] = get_avatar()
            # if uid.isdigit() and DISCORD_TOKEN:  # Probably a valid ID, let's try and hit the API
            #     with requests.get(f'{DISCORD_API_URL}/{uid}', headers=DISCORD_HEADERS) as r:
            #         _user = r.json()
            #         if not _user.get('message'):  # No error code, so Discord found the user
            #             user = _user
            #             if user.get('avatar') is not None:
            #                 user['avatar'] = get_avatar()

            user['avatar'] = user['avatar'] or get_avatar(default_avatar=True)
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

        messages.append(SerializedMessage(message_dict).__dict__)

        progress_recorder.set_progress(count + 1, total)

    def sort_chronological(value):
        return int(value.get('message_id') or 0) or dateutil.parser.parse(value.get('timestamp'))

    messages.sort(key=sort_chronological)
    data['messages'] = messages

    def sort_alphabetical(value):
        return value['name']

    users.sort(key=sort_alphabetical)
    data['users'] = users

    return data


@shared_task(bind=True)
def create_log(self, data: dict, create_data):
    progress_recorder = ProgressRecorder(self)
    variant = create_data.pop('variant')
    create_data['log_type'] = variant[0] if variant else create_data['log_type']
    messages = data.pop('messages')
    create_data['data'] = data
    if create_data['author']:
        create_data['author'] = list(serializers.deserialize('json', create_data['author']))[0].object
    expires = create_data.pop('expires')
    create_data['expires_at'] = datetime.now(tz=pytz.UTC) + timedelta(seconds=expires)
    progress_recorder.set_progress(1, 2)
    created_log = create_log_entry(**create_data, messages=messages)
    progress_recorder.set_progress(2, 2)
    return created_log.short_code
