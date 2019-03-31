import json
import re

import requests

from django_logs.models import *
from django.conf import settings

DISCORD_TOKEN = getattr(settings, 'LOG_DISCORD_TOKEN', None)

DISCORD_API_URL = 'https://discordapp.com/api/v7/users'

DISCORD_HEADERS = {'Authorization': DISCORD_TOKEN}

rowboat_re = r'(?P<time>[\d\-\: \.]{26}) \((?P<mid>[\d]{16,18}) \/ (?P<gid>[\d]{16,18}) \/ ' \
             r'(?P<uid>[\d]{16,18})\) (?P<uname>.*)#(?P<disc>\d{4}): (?P<content>[\S\s]*?) ' \
             r'\((?P<attach>(?:http(?:|s):.*))?\)'

rosalina_bottings_re = r'(?P<time>(?:[\d-]{10})T(?:[\d:.]{15}))\+[\d:]{5} \| (?P<gname>.*?)\[(?P<gid>\d{16,18})\]' \
             r' \|  (?P<cname>[\w-]{1,100})\[(?P<cid>\d{16,18})\] \| (?P<uname>.*?)\[(?P<uid>\d{16,18})' \
             r'\] \| said: (?P<content>[\S\s]*?)\nMessage ID: (?P<mid>\d{16,18})'

giraffeduck_re = r'\[(?P<time>[\d\-\ \:]{19})\] \((?P<mid>\d{16,18})\) (?P<uname>.*)#(?P<disc>\d{4}) : ' \
                 r'(?P<content>[\S\s]*?) \| Attach: (?P<attach>(?:http(?:|s):.*))? \| RichEmbed: ' \
                 r'(?P<embeds>null|.*)'

auttaja_re = r'\[(?P<time>[\w :]{24})\] \((?P<uname>.*)#(?P<disc>\d{4}) - (?P<uid>\d{16,18})\) \[(?P<mid>\d{16,18})' \
             r'\]: (?P<content>[\S\s]*)'

logger_re = r'(?P<uname>.*)#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) \| (?P<time>[\w :-]{33}) \(\w{3,4}\): ' \
            r'(?P<content>[\S\s]*?)(?: ======> Contains Embed)?(?: =====> Attachment: (?P<filename>[\w.]+):' \
            r'(?P<attach>(?:http(?:|s):.*)))?$'

sajuukbot_re = r'\[(?P<time>[\w :.-]{26})\] (?P<uname>.*)#(?P<disc>\d{4}) \((?P<mid>[\d]{16,18}) \/ (?P<uid>[\d]' \
               r'{16,18}) \/ (?P<cid>[\d]{16,18})\): (?P<content>[\S\s]*?)(?: \((?P<attach>(?:http(?:|s):.*))\))?'

spectra_re = r'\[(?P<time>[\w, :]{29})\] (?P<uname>.*)#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) : (?P<content>[\S\s]*?)' \
             r'(?: ?(?P<attach>(?:http(?:|s):.*)))?$'

gearboat_re = r'(?P<time>[\w\-. :]{26}) (?P<gid>\d{16,18}) - (?P<cid>\d{16,18}) - (?P<mid>\d{16,18}) \| (?P<uname>.*)' \
              r'#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) \| (?P<content>[\S\s]*?) \| (?:(?P<attach>(?:http(?:|s):.*)) ' \
              r'?)?'


class LogParser:

    def __init__(self, log_type):
        self.log_type = log_type

    def create(self, content, url):
        log_type = self.log_type
        data, short_code = self.parse(content)
        if LogRoute.objects.filter(url=url).exists():
            LogRoute.objects.filter(url=url).update(log_type=log_type, data=data)
        if LogRoute.objects.filter(short_code=short_code).exists():
            return short_code, False
        log, created = LogRoute.objects.get_or_create(url=url, log_type=log_type, data=data)
        return log.short_code, created

    def parse(self, content):
        log_type = self.log_type
        parser = getattr(self, f'_parse_{log_type}')
        data = parser(content)
        short_code = LogRoute.generate_short_code(data)
        return data, short_code

    @staticmethod
    def _get_attach_info(attachments: list):
        attach = []
        if len(attachments) > 0 and attachments[0] != '':
            for url in attachments:
                attach_info = {'id': url.rsplit('/', 2)[1], 'filename': url.rsplit('/', 2)[2], 'url': url, 'size': 0,
                               'is_image': False, 'error': False}
                try:
                    req = requests.head(url)
                except requests.exceptions.MissingSchema:
                    req = requests.head('https://' + url)
                if req.status_code == 200:
                    if req.headers['Content-Type'].split('/')[0] == 'image':
                        attach_info['is_image'] = True
                else:
                    attach_info['error'] = True
                attach.append(attach_info)
        return attach

    @staticmethod
    def _parse(data: dict, match_data: list):
        users = list()
        _users = dict()
        data['messages'] = list()

        for match in match_data:
            uid = match['uid']
            message_dict = {'message_id': match.get('mid', None), 'timestamp': match['time'],
                            'content': match['content']}

            user = {'id': uid, 'username': match.get('uname', 'Unknown User'), 'discriminator': match.get('disc', '0000'
                                                                                                          )}
            if uid not in _users:
                if DISCORD_TOKEN is None:
                    default = int(user['discriminator']) % 5
                    user['avatar'] = f'https://cdn.discordapp.com/embed/avatars/{default}.png'
                else:
                    with requests.get(f'{DISCORD_API_URL}/{uid}', headers=DISCORD_HEADERS) as r:
                        _user = r.json()
                        if _user.get('message', None):  # Discord can't find the user, so default avatar
                            default = int(user['discriminator']) % 5
                            user['avatar'] = f'https://cdn.discordapp.com/embed/avatars/{default}.png'
                        else:
                            user = _user
                            if user.get('avatar', None) is not None:
                                ending = 'gif' if user['avatar'].startswith('a_') else 'png'
                                user['avatar'] = f'https://cdn.discordapp.com/avatars/{uid}/{user["avatar"]}.{ending}'
                            else:
                                default = int(user['discriminator']) % 5
                                user['avatar'] = f'https://cdn.discordapp.com/embed/avatars/{default}.png'
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

            data['messages'].append(message_dict)

        data['users'] = users

        return data

    def _parse_rowboat(self, content):
        data = dict()
        data['raw_content'] = content
        data['messages'] = list()
        matches = list(re.finditer(rowboat_re, content))
        match_data = list()

        for match in matches:
            match_info = match.groupdict()
            match_info['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] is not None \
                else []
            match_data.append(match_info)

        data = self._parse(data, match_data)
        data['type'] = 'Rowboat'

        return data

    def _parse_rosalina_bottings(self, content):
        data = dict()
        data['raw_content'] = content
        data['messages'] = list()
        matches = list(re.finditer(rosalina_bottings_re, content))

        match_data = list(m.groupdict() for m in matches)
        data = self._parse(data, match_data)
        data['type'] = 'Rosalina Bottings'

        return data

    def _parse_giraffeduck(self, content):
        data = dict()
        match_data = list()
        data['raw_content'] = content
        data['messages'] = list()
        matches = list(re.finditer(giraffeduck_re, content))

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

        for match in matches:
            match = match.groupdict()
            match['uid'] = users[f'{match["uname"]}#{match["disc"]}']
            _attach = match['attach'].split(', ')
            match['attach'] = self._get_attach_info(_attach)
            match['embeds'] = [json.loads(match['embeds'])] if match['embeds'] != 'null' else []
            match['content'] = re.sub(r'(<@!?(\d+)>)', lambda m: f'<@{user_mentions[m.group(2)]} ({m.group(2)})>',
                                      match['content'])
            match['content'] = re.sub(r'(<#(\d+)>)', lambda m: f'<#{channel_mentions[m.group(2)]}>', match['content'])
            match['content'] = re.sub(r'(<@&(\d+)>)', lambda m: f'<@&{role_mentions[m.group(2)]}>', match['content'])

            match_data.append(match)

        data = self._parse(data, match_data)
        data['type'] = 'GiraffeDuck'

        return data

    def _parse_auttaja(self, content):
        content = re.sub('\r\n', '\n', content)
        content = content[:-1] if content.endswith('\n') else content
        data = dict()
        data['raw_content'] = content
        data['messages'] = list()
        lines = re.split('\n\n', content)
        _matches = list()
        for text in lines:
            if re.match(auttaja_re, text):
                _matches.append(text)
            else:
                _matches[len(_matches) - 1] = _matches[len(_matches) - 1] + f'\n\n{text}'

        matches = list(re.match(auttaja_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches)
        for match in match_data:
            match['time'] = datetime.strptime(match['time'], '%a %b %d %H:%M:%S %Y').isoformat()
        data = self._parse(data, match_data)
        data['type'] = 'Auttaja'

        return data

    def _parse_logger(self, content):
        data = dict()
        data['raw_content'] = content
        data['messages'] = list()
        content = re.sub('\r\n', '\n', content)
        lines = re.split('\n', content)
        _matches = list()
        for text in lines:
            if re.match(logger_re, text):
                _matches.append(text)
            else:
                _matches[len(_matches) - 1] = _matches[len(_matches) - 1] + f'\n\n{text}'

        matches = list(re.match(logger_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches)
        for match in match_data:
            match['time'] = datetime.strptime(match['time'], '%a %b %d %Y %H:%M:%S GMT%z').isoformat()
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] is not None else []
        data = self._parse(data, match_data)
        data['type'] = 'Logger'

        return data

    def _parse_sajuukbot(self, content):
        data = dict()
        data['raw_content'] = content
        data['messages'] = list()
        lines = re.split('\n', content)
        _matches = list()
        for text in lines:
            if re.match(sajuukbot_re, text):
                _matches.append(text)
            else:
                _matches[len(_matches) - 1] = _matches[len(_matches) - 1] + f'\n\n{text}'

        matches = list(re.match(sajuukbot_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches)
        for match in match_data:
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] is not None else []
        data = self._parse(data, match_data)
        data['type'] = 'SajuukBot'

        return data

    def _parse_spectra(self, content):
        data = dict()
        data['raw_content'] = content
        data['messages'] = list()
        content = re.sub('\r\n', '\n', content)
        lines = re.split('\n\n', content)[1:]
        _matches = list()
        for text in lines:
            if re.match(spectra_re, text):
                _matches.append(text)
            else:
                _matches[len(_matches) - 1] = _matches[len(_matches) - 1] + f'\n\n{text}'

        matches = list(re.match(spectra_re, m) for m in _matches)
        match_data = list(m.groupdict() for m in matches)
        for match in match_data:
            match['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] is not None else []
        data = self._parse(data, match_data)
        data['type'] = 'Spectra'

        return data

    def _parse_gearboat(self, content):
        data = dict()
        data['raw_content'] = content
        data['messages'] = list()
        matches = list(re.finditer(gearboat_re, content))
        match_data = list()

        for match in matches:
            match_info = match.groupdict()
            match_info['attach'] = self._get_attach_info(match['attach'].split(', ')) if match['attach'] is not None \
                else []
            match_data.append(match_info)

        data = self._parse(data, match_data)
        data['type'] = 'GearBoat'

        return data
