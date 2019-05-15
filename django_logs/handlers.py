import re
from datetime import datetime

from django_logs.consts import rowboat_re, rosalina_bottings_re, giraffeduck_re, auttaja_re, logger_re, sajuukbot_re, \
    vortex_re, gearbot_re, capnbot_re, modmailbot_re
from django_logs.utils import get_attach_info, get_embed_info


def rowboat(content, **kwargs):
    data = dict()
    matches = (re.finditer(rowboat_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    for match in match_data:
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

    data['type'] = 'Rowboat'
    if kwargs['variant']:
        variant = kwargs.pop('variant')
        data['type'] = variant[1]

    return data, match_data


def rosalina_bottings(content, **kwargs):
    data = dict()
    matches = (re.finditer(rosalina_bottings_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    data['type'] = 'Rosalina Bottings'

    return data, match_data


def giraffeduck(content, **kwargs):
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
        match['attach'] = get_attach_info(_attach)
        match['embeds'] = [get_embed_info(match['embeds'])] if match['embeds'] else []
        match['content'] = re.sub(r'<@!?(\d+)>', lambda m: f'<@{user_mentions[m.group(1)]} ({m.group(1)})>',
                                  match['content'])
        match['content'] = re.sub(r'<#(\d+)>', lambda m: f'<#{channel_mentions[m.group(1)]}>', match['content'])
        match['content'] = re.sub(r'<@&(\d+)>', lambda m: f'<@&{role_mentions[m.group(1)]}>', match['content'])

    data['type'] = 'GiraffeDuck'

    return data, match_data


def auttaja(content, **kwargs):
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
        match['attach'] = get_attach_info(match['attach'].split(' ')) if match['attach'] else []

    data['type'] = 'Auttaja'

    return data, match_data


def logger(content, **kwargs):
    data = dict()
    matches = (re.finditer(logger_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    for match in match_data:
        match['embeds'] = get_embed_info(match['embeds'])['embeds'] if match['embeds'] else []
        match['time'] = datetime.strptime(match['time'], '%a %b %d %Y %H:%M:%S GMT%z').isoformat()
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

    data['type'] = 'Logger'

    return data, match_data


def sajuukbot(content, **kwargs):
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
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

    data['type'] = 'SajuukBot'

    return data, match_data


def vortex(content, **kwargs):
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
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

    data['type'] = 'Vortex'

    return data, match_data


def gearbot(content, **kwargs):
    data = dict()
    matches = (re.finditer(gearbot_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    for match in match_data:
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

    data['type'] = 'GearBot'

    return data, match_data


def capnbot(content, **kwargs):
    data = dict()
    matches = (re.finditer(capnbot_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    for match in match_data:
        match['embeds'] = get_embed_info(match['embeds'])['embeds'] if match['embeds'] else []
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

    data['type'] = 'CapnBot'

    return data, match_data


def modmailbot(content, **kwargs):
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
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

    data['type'] = 'ModMailBot'

    return data, match_data
