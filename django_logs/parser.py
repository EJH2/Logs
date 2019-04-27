import ast
from datetime import datetime
import json
import re

import dateutil
import requests

from django_logs.models import LogRoute, User, SerializedMessage
from django.conf import settings

DISCORD_TOKEN = getattr(settings, 'LOG_DISCORD_TOKEN', None)

DISCORD_API_URL = 'https://discordapp.com/api/v7/users'

DISCORD_HEADERS = {'Authorization': DISCORD_TOKEN}

rowboat_re = r'(?P<time>[\d\-\: \.]{26}) \((?P<mid>[\d]{16,18}) \/ (?P<gid>[\d]{16,18}) \/ (?P<uid>[\d]{16,18})\) ' \
             r'(?P<uname>.*?)#(?P<disc>\d{4}): (?P<content>[\S\s]*?)? \((?P<attach>(?:http(?:|s):.*))?\)$'

rosalina_bottings_re = r'(?P<time>(?:[\d-]{10})T(?:[\d:.]{8,15}))(?:\+[\d:]{5}|Z) \| (?P<gname>.*?)\[(?P<gid>\d{16,' \
                       r'18})\] \|  (?P<cname>[\w-]{1,100})\[(?P<cid>\d{16,18})\] \| (?P<uname>.*?)\[(?P<uid>\d{16,' \
                       r'18})\] \| said: (?P<content>[\S\s]*?)(?:\nAttachment: (?P<attach>(?:http(?:|s):.*)))?\nMess' \
                       r'age ID: (?P<mid>\d{16,18})$'

giraffeduck_re = r'\[(?P<time>[\d\-\ \:]{19})\] \((?P<mid>\d{16,18})\) (?P<uname>.*?)#(?P<disc>\d{4}) : (?P<content>' \
                 r'[\S\s]*?)? \| Attach: (?P<attach>(?:http(?:|s):.*))? \| RichEmbed: (?:null|(?P<embeds>.*))$'

auttaja_re = r'\[(?P<time>[\w :]{24,25})\] \((?P<uname>.*?)#(?P<disc>\d{4}) - (?P<uid>\d{16,18})\) \[(?P<mid>\d{16,18' \
             r'})\]: (?P<content>[\S\s]*?)(?: (?P<attach>(?:http(?:|s):.*))?)?$'

logger_re = r'(?P<uname>.*?)#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) \| \((?:(?:https://(?:cdn\.)?discordapp\.com/(?:' \
            r'avatars/\d{16,18}|assets)/(?P<avatar>\w+)\.\w{3,4}(?:\?[\w=]+)?))\) \| (?P<time>[\w :-]{33}) \(' \
            r'[\w ]+\): (?P<content>[\S\s]*?) \| (?P<embeds>(?:{\"embeds\": \[.*?))? \| (?: =====> Attachment:.*?:' \
            r'(?P<attach>(?:http(?:|s):.*)))?$'

sajuukbot_re = r'\[(?P<time>[\w :.-]{26})\] (?P<uname>.*?)#(?P<disc>\d{4}) \((?P<mid>[\d]{16,18}) \/ (?P<uid>[\d]' \
               r'{16,18}) \/ (?P<cid>[\d]{16,18})\): (?P<content>[\S\s]*?)(?: \((?P<attach>(?:http(?:|s):.*))\))?'

vortex_re = r'\[(?P<time>[\w, :]{28,29})\] (?P<uname>.*?)#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) : (?P<content>[\S\s' \
            r']+?)?(?: ?(?P<attach>(?:http(?:|s):.*)))?$'

gearboat_re = r'(?P<time>[\w\-. :]{26}) (?P<gid>\d{16,18}) - (?P<cid>\d{16,18}) - (?P<mid>\d{16,18}) \| (?P<uname>.*?' \
              r')#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) \| (?P<content>[\S\s]*?)? \|(?: ?(?P<attach>(?:http(?:|s):.*' \
              r'))?)?$'

capnbot_re = r'(?P<time>[\d\-\: \.]{19,26}) \((?P<mid>[\d]{16,18}) \/ (?P<gid>[\d]{16,18}) \/ (?P<uid>[\d]{16,18})\) ' \
             r'\((?:(?:https://(?:cdn\.)?discordapp\.com/(?:avatars/\d{16,18}|(?P<asset>assets))/(?P<avatar>\w+)\.\w' \
             r'{3,4}(?:\?[\w=]+)?))\) (?P<uname>.*?)#(?P<disc>\d{4}): (?P<content>[\S\s]*?)? \| (?P<attach>(?:http(?' \
             r':|s):.*))? \| (?P<embeds>(?:{\"embeds\": \[).*?)?$'

modmailbot_re = r'\[(?P<time>[\d :-]{19})\](?:(?: \[FROM USER\]| \[TO USER\] (?:\(Anonymous\) )?\(.*?\))? (?P<uname>' \
                r'.*?)(?:#(?P<disc>\d{4}))?: (?P<content>[\S\s]*?)(?:\n{2}\*\*Attachment:\*\* .*? \(.*\)\n(?P<attach' \
                r'>(?:http(?:|s):.*)))?$| (?P<bcontent>[^\n]+))'

attachment_re = r'(?:http(?:s|):\/\/)(?:images-ext-\d|cdn|media).discordapp\.(?:com|net)\/(?:attachments(?:\/\d{16,18' \
                r'}){2}|external\/[^\/]+)\/(?P<filename>.*)'


class LogParser:

    def __init__(self, log_type):
        self.log_type = log_type

    @staticmethod
    def _get_messages(data):
        _msgs = data.pop('messages')

        def sort_chronological(value):
            return int(value.get('message_id') or 0) or dateutil.parser.parse(value.get('timestamp'))

        _msgs.sort(key=sort_chronological)
        return _msgs

    def _update_db(self, objects, create_data):
        messages = self._get_messages(create_data['data'])
        short_code = create_data.pop('short_code')
        first = objects[0]
        assert isinstance(first, LogRoute)

        # These messages don't need chunking
        if len(messages) <= 1000 and first.chunked is False:
            return objects.update(**create_data, messages=messages, short_code=f'{short_code}')
        if len(messages) <= 1000 and first.chunked is True:
            objects.delete()
            return LogRoute.objects.create(**create_data, messages=messages, short_code=f'{short_code}')

        # These messages do
        objects.delete()  # Wipe the row(s) so no old info is left over
        self._create_chunked(messages, create_data, short_code)

    def _create_chunked(self, messages, create_data, short_code):
        batch_list = list()
        for batch in range(0, len(messages), 1000):
            batch_list.append(messages[batch:batch + 1000])  # Split messages by the 1000
        create_data['chunked'] = True
        new_first = LogRoute(**create_data, short_code=f'{short_code}-0', messages=batch_list[0])
        create_data['data'] = None
        create_data['content'] = None
        new_rest = (LogRoute(**create_data, short_code=f'{short_code}-{i}', messages=batch_list[i]) for i in range(
            1, len(batch_list)))
        new_objects = [new_first, *new_rest]
        logs = LogRoute.objects.bulk_create(new_objects)
        return logs[0], True

    def create(self, content, origin, *, new=False):
        url = None
        if isinstance(origin, tuple):
            url = origin[1]
            origin = 'url'
        short_code = LogRoute.generate_short_code(content)
        filter_url = LogRoute.objects.filter(url=url).filter(url__isnull=False).order_by('id')
        if filter_url.exists():
            if not new:
                return short_code, False
        filter_short = LogRoute.objects.filter(short_code__startswith=short_code)
        if filter_short.exists():
            if not new:
                return short_code, False
            filter_short.delete()
        data = self.parse(content)
        create_data = {'origin': origin, 'url': url, 'short_code': short_code, 'log_type': self.log_type, 'data': data,
                       'content': content}
        if url and filter_url.exists():
            self._update_db(filter_url, create_data)
        messages = self._get_messages(data)
        chunked = len(messages) > 1000
        if chunked:
            short_code = create_data.pop('short_code')
            _, created = self._create_chunked(messages, create_data, short_code)
        else:
            _, created = LogRoute.objects.get_or_create(**create_data, messages=messages)
        return short_code, created

    def parse(self, content):
        parser = getattr(self, f'_parse_{self.log_type}')
        data = parser(content)
        return data

    @staticmethod
    def _get_attach_info(attachments: list):
        attach = []
        if len(attachments) > 0 and attachments[0] != '':
            for url in attachments:
                match = re.match(attachment_re, url)
                file = match.group('filename') if match else url.rsplit('/', 1)[-1]
                attach_info = {'filename': file, 'url': url, 'size': 0, 'is_image': False}
                if file.rsplit('.', 1)[-1] in ['png', 'jpg', 'jpeg', 'gif', 'webm', 'webp', 'mp4']:
                    attach_info['is_image'] = True
                attach.append(attach_info)
        return attach

    @staticmethod
    def _get_embed_info(embeds: str):
        try:
            return json.loads(embeds)
        except json.decoder.JSONDecodeError:
            try:
                return ast.literal_eval(embeds)  # I'M SORRY
            except AttributeError:
                return dict()

    @staticmethod
    def _parse(data: dict, match_data: list):
        users = list()
        _users = dict()
        messages = list()

        for match in match_data:
            uid = match.get('uid')
            message_dict = {'message_id': match.get('mid'), 'timestamp': match['time'],
                            'content': match['content']}

            user = {'id': uid, 'username': match.get('uname') or 'Unknown User',
                    'discriminator': match.get('disc') or '0000', 'avatar': match.get('avatar')}

            if not uid:
                uid = f'{user["username"]}#{user["discriminator"]}'

            def get_avatar(default_avatar: bool = False):
                if not user.get('avatar') or default_avatar:
                    default = int(user['discriminator']) % 5
                    return f'https://cdn.discordapp.com/embed/avatars/{default}.png'
                if match.get('asset'):
                    return f'https://discordapp.com/assets/{user["avatar"]}.png'
                ending = 'gif' if user['avatar'].startswith('a_') else 'png'
                return f'https://cdn.discordapp.com/avatars/{uid}/{user["avatar"]}.{ending}'

            if uid not in _users:
                if user.get('avatar'):  # User supplied avatar, don't bombard Discord's API
                    user['avatar'] = get_avatar()
                    pass
                elif not DISCORD_TOKEN:  # We can't request the API, so use the default avatar
                    pass
                else:
                    if uid.isdigit():
                        with requests.get(f'{DISCORD_API_URL}/{uid}', headers=DISCORD_HEADERS) as r:
                            _user = r.json()
                            if not _user.get('message'):  # No error code, so Discord found the user
                                user = _user
                                if user.get('avatar') is not None:
                                    user['avatar'] = get_avatar()

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

        data['messages'] = messages

        def sort_alphabetical(value):
            return value['name']

        users.sort(key=sort_alphabetical)
        data['users'] = users

        return data

    def _parse_rowboat(self, content):
        data = dict()
        matches = (re.finditer(rowboat_re, content, re.MULTILINE))
        match_data = list(m.groupdict() for m in matches)

        for match in match_data:
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'Rowboat'

        return data

    def _parse_rosalina_bottings(self, content):
        data = dict()
        matches = (re.finditer(rosalina_bottings_re, content, re.MULTILINE))
        match_data = list(m.groupdict() for m in matches)

        data = self._parse(data, match_data)
        data['type'] = 'Rosalina Bottings'

        return data

    def _parse_giraffeduck(self, content):
        data = dict()
        matches = (re.finditer(giraffeduck_re, content, re.MULTILINE))
        match_data = list(m.groupdict() for m in matches)

        headers = content.split('\n')[:5]
        header_info = list()
        for header in headers:  # Splits headers into [('name', 'id'),...]
            _headers = list(zip(*[iter(re.split(r' \((\d{16,18})\)(?:; |)', header[1:-1])[:-1])] * 2))
            header_info.append(_headers)
        users = dict()
        user_mentions = dict()
        channel_mentions = dict()
        role_mentions = dict()
        for user in header_info[1]:
            users[user[0]] = user[1]
        for mention in header_info[2]:  # Mentions
            user_mentions[mention[1]] = mention[0]  # {'id': 'user'}
        for channel in header_info[3]:  # Channels
            channel_mentions[channel[1]] = channel[0]
        for role in header_info[4]:  # Roles
            role_mentions[role[1]] = role[0]

        for match in match_data:
            match['uid'] = users[f'{match["uname"]}#{match["disc"]}']
            _attach = match['attach'].split(', ') if match['attach'] else []
            match['attach'] = self._get_attach_info(_attach)
            match['embeds'] = [self._get_embed_info(match['embeds'])] if match['embeds'] else []
            match['content'] = re.sub(r'<@!?(\d+)>', lambda m: f'<@{user_mentions[m.group(1)]} ({m.group(1)})>',
                                      match['content'])
            match['content'] = re.sub(r'<#(\d+)>', lambda m: f'<#{channel_mentions[m.group(1)]}>', match['content'])
            match['content'] = re.sub(r'<@&(\d+)>', lambda m: f'<@&{role_mentions[m.group(1)]}>', match['content'])

        data = self._parse(data, match_data)
        data['type'] = 'GiraffeDuck'

        return data

    def _parse_auttaja(self, content):
        content = content[:-1] if content.endswith('\n') else content
        data = dict()
        lines = content.split('\n\n')
        _matches = list()
        for text in lines:
            if re.match(auttaja_re, text):
                _matches.append(text)
            else:
                _matches[-1] += f'\n\n{text}'

        matches = (re.match(auttaja_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches)

        for match in match_data:
            match['time'] = datetime.strptime(match['time'], '%a %b %d %H:%M:%S %Y').isoformat()
            match['attach'] = self._get_attach_info(match['attach'].split(' ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'Auttaja'

        return data

    def _parse_logger(self, content):
        data = dict()
        matches = (re.finditer(logger_re, content, re.MULTILINE))
        match_data = list(m.groupdict() for m in matches)

        for match in match_data:
            match['embeds'] = self._get_embed_info(match['embeds'])['embeds'] if match['embeds'] else []
            match['time'] = datetime.strptime(match['time'], '%a %b %d %Y %H:%M:%S GMT%z').isoformat()
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'Logger'

        return data

    def _parse_sajuukbot(self, content):
        data = dict()
        lines = content.split('\n')
        _matches = list()
        for text in lines:
            if re.match(sajuukbot_re, text):
                _matches.append(text)
            else:
                _matches[-1] += f'\n{text}'

        matches = (re.match(sajuukbot_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches)

        for match in match_data:
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'SajuukBot'

        return data

    def _parse_vortex(self, content):
        data = dict()
        lines = content.split('\n\n')[1:]
        _matches = list()
        for text in lines:
            if re.match(vortex_re, text):
                _matches.append(text)
            else:
                _matches[-1] += f'\n\n{text}'

        matches = (re.match(vortex_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches)

        for match in match_data:
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'Vortex'

        return data

    def _parse_gearboat(self, content):
        data = dict()
        matches = (re.finditer(gearboat_re, content, re.MULTILINE))
        match_data = list(m.groupdict() for m in matches)

        for match in match_data:
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'GearBoat'

        return data

    def _parse_capnbot(self, content):
        data = dict()
        matches = (re.finditer(capnbot_re, content, re.MULTILINE))
        match_data = list(m.groupdict() for m in matches)

        for match in match_data:
            match['embeds'] = self._get_embed_info(match['embeds'])['embeds'] if match['embeds'] else []
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'CapnBot'

        return data

    def _parse_modmailbot(self, content):
        data = dict()
        content = '────────────────\n'.join(content.split('────────────────\n')[1:])  # Gets rid of useless header
        lines = content.split('\n')
        _matches = list()
        for text in lines:
            if re.match(modmailbot_re, text):
                _matches.append(text)
            else:
                _matches[-1] += f'\n{text}'

        matches = (re.match(modmailbot_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches if not m.group('bcontent'))

        for match in match_data:
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        data = self._parse(data, match_data)
        data['type'] = 'ModMailBot'

        return data
