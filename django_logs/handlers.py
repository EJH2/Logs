import re
from datetime import datetime

from django_logs.consts import rowboat_re, rosalina_bottings_re, giraffeduck_re, auttaja_re, logger_re, sajuukbot_re, \
    vortex_re, gearbot_re, capnbot_re, modmailbot_re, invite_deleter_re
from django_logs.utils import get_attach_info, get_embed_info


def rowboat(content, progress):
    matches = (re.finditer(rowboat_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)

    for count, match in enumerate(match_data):
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def rosalina_bottings(content, progress):
    matches = (re.finditer(rosalina_bottings_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)
    progress.set_progress(total, total)

    return match_data


def giraffeduck(content, progress):
    matches = (re.finditer(giraffeduck_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data) + 4

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
    progress.set_progress(1, total)
    for mention in header_info[2]:  # Mentions
        user_mentions[mention[1]] = mention[0]  # {'id': 'user'}
    progress.set_progress(2, total)
    for channel in header_info[3]:  # Channels
        channel_mentions[channel[1]] = channel[0]
    progress.set_progress(3, total)
    for role in header_info[4]:  # Roles
        role_mentions[role[1]] = role[0]
    progress.set_progress(4, total)

    for count, match in enumerate(match_data):
        match['time'] = datetime.strptime(match['time'], '%Y-%d-%m %H:%M:%S').isoformat()
        match['uid'] = users[f'{match["uname"]}#{match["disc"]}']
        _attach = match['attach'].split(', ') if match['attach'] else []
        match['attach'] = get_attach_info(_attach)
        match['embeds'] = get_embed_info(match['embeds']) if match['embeds'] else []
        match['content'] = re.sub(r'<@!?(\d+)>', lambda m: f'<@{user_mentions[m.group(1)]} ({m.group(1)})>',
                                  match['content'])
        match['content'] = re.sub(r'<#(\d+)>', lambda m: f'<#{channel_mentions[m.group(1)]}>', match['content'])
        match['content'] = re.sub(r'<@&(\d+)>', lambda m: f'<@&{role_mentions[m.group(1)]}>', match['content'])

        progress.set_progress(count + 4, total)

    return match_data


def auttaja(content, progress):
    content = content[:-1] if content.endswith('\n') else content
    lines = content.split('\n\n')
    _matches = list()
    for text in lines:
        if re.match(auttaja_re, text):
            _matches.append(text)
        else:
            _matches[-1] += f'\n\n{text}'

    matches = (re.match(auttaja_re, m) for m in _matches)
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)

    for count, match in enumerate(match_data):
        match['time'] = datetime.strptime(match['time'], '%a %b %d %H:%M:%S %Y').isoformat()
        match['attach'] = get_attach_info(match['attach'].split(' ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def logger(content, progress):
    matches = (re.finditer(logger_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)
    
    total = len(match_data)

    for count, match in enumerate(match_data):
        match['embeds'] = get_embed_info(match['embeds'])['embeds'] if match['embeds'] else []
        match['time'] = datetime.strptime(match['time'], '%a %b %d %Y %H:%M:%S GMT%z').isoformat()
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def sajuukbot(content, progress):
    lines = content.split('\n')
    _matches = list()
    for text in lines:
        if re.match(sajuukbot_re, text):
            _matches.append(text)
        else:
            _matches[-1] += f'\n{text}'

    matches = (re.match(sajuukbot_re + r'$', m) for m in _matches)
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)

    for count, match in enumerate(match_data):
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def vortex(content, progress):
    lines = content.split('\n\n')[1:]
    _matches = list()
    for text in lines:
        if re.match(vortex_re, text):
            _matches.append(text)
        else:
            _matches[-1] += f'\n\n{text}'

    matches = (re.match(vortex_re, m) for m in _matches)
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)

    for count, match in enumerate(match_data):
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def gearbot(content, progress):
    matches = (re.finditer(gearbot_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)

    for count, match in enumerate(match_data):
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def capnbot(content, progress):
    matches = (re.finditer(capnbot_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)

    for count, match in enumerate(match_data):
        match['embeds'] = get_embed_info(match['embeds'])['embeds'] if match['embeds'] else []
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def modmailbot(content, progress):
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

    total = len(match_data)

    for count, match in enumerate(match_data):
        match['attach'] = get_attach_info(match['attach'].split(', ')) if match['attach'] else []

        progress.set_progress(count + 1, total)

    return match_data


def invite_deleter(content, progress):
    lines = content.split('\n')
    _matches = list()
    for text in lines:
        if re.match(invite_deleter_re, text):
            _matches.append(text)
        else:
            _matches[-1] += f'\n{text}'

    matches = (re.match(invite_deleter_re + r'$', m) for m in _matches)
    match_data = list(m.groupdict() for m in matches)

    total = len(match_data)

    for count, match in enumerate(match_data):
        progress.set_progress(count + 1, total)

    return match_data
