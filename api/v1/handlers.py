import re
from datetime import datetime

from api import consts


def rowboat(content, progress):
    matches = (re.finditer(consts.rowboat_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)
    message_array = []

    total = len(match_data)

    for count, match in enumerate(match_data):
        message_array.append({
            'id': match['message_id'],
            'guild_id': match['guild_id'],
            'author': {
                'id': match['user_id'],
                'username': match['username'],
                'discriminator': match['discriminator']
            },
            'content': match['content'],
            'timestamp': datetime.strptime(match['timestamp'], '%Y-%m-%d %H:%M:%S.%f').isoformat(),
            'attachments': [
                {
                    'filename': url.rsplit('/', 1)[1],
                    'url': url
                }
                for url in (match['attachments'].split(', ') if match.get('attachments') else [])
            ]
        })

        progress.set_progress(count + 1, total)

    return message_array


def rosalina_bottings(content, progress):
    matches = (re.finditer(consts.rosalina_bottings_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)
    message_array = []

    total = len(match_data)

    for count, match in enumerate(match_data):
        message_array.append({
            'id': match['message_id'],
            'channel_id': match['channel_id'],
            'guild_id': match['guild_id'],
            'author': {
                'id': match['user_id'],
                'username': match['username'],
                'discriminator': match['discriminator']
            },
            'content': match['content'],
            'timestamp': match['timestamp'],
            'attachments': [
                {
                    'filename': url.rsplit('/', 1)[1],
                    'url': url
                }
                for url in (match['attachments'].split(', ') if match.get('attachments') else [])
            ]
        })

        progress.set_progress(count + 1, total)

    return message_array


def auttaja(content, progress):
    content = content[:-1] if content.endswith('\n') else content
    lines = content.split('\n\n')
    _matches = list()
    for text in lines:
        if re.match(consts.auttaja_re, text):
            _matches.append(text)
        else:
            _matches[-1] += f'\n\n{text}'

    matches = (re.match(consts.auttaja_re, m) for m in _matches)
    match_data = list(m.groupdict() for m in matches)
    message_array = []

    total = len(match_data)

    for count, match in enumerate(match_data):
        message_array.append({
            'id': match['message_id'],
            'author': {
                'id': match['user_id'],
                'username': match['username'],
                'discriminator': match['discriminator']
            },
            'content': match['content'],
            'timestamp': datetime.strptime(match['timestamp'], '%a %b %d %H:%M:%S %Y').isoformat(),
            'attachments': [
                {
                    'filename': url.rsplit('/', 1)[1],
                    'url': url
                }
                for url in (match['attachments'].split(' ') if match.get('attachments') else [])
            ]
        })

        progress.set_progress(count + 1, total)

    return match_data


def gearbot(content, progress):
    matches = (re.finditer(consts.gearbot_re, content, re.MULTILINE))
    match_data = list(m.groupdict() for m in matches)
    message_array = []

    total = len(match_data)

    for count, match in enumerate(match_data):
        message_array.append({
            'id': match['message_id'],
            'channel_id': match['channel_id'],
            'guild_id': match['guild_id'],
            'author': {
                'id': match['user_id'],
                'username': match['username'],
                'discriminator': match['discriminator']
            },
            'content': match['content'],
            'timestamp': datetime.strptime(match['timestamp'], '%Y-%m-%d %H:%M:%S.%f').isoformat(),
            'attachments': [
                {
                    'filename': url.rsplit('/', 1)[1],
                    'url': url
                }
                for url in (match['attachments'].split(', ') if match.get('attachments') else [])
            ]
        })

        progress.set_progress(count + 1, total)

    return message_array


def modmailbot(content, progress):
    content = '────────────────\n'.join(content.split('────────────────\n')[1:])  # Gets rid of useless header
    _matches = list()
    for text in content.split('\n'):
        if re.match(consts.modmailbot_re, text):
            _matches.append(text)
        else:
            _matches[-1] += f'\n{text}'

    matches = (re.match(consts.modmailbot_re, m) for m in _matches)
    match_data = list(m.groupdict() for m in matches if not m.group('bcontent'))
    message_array = []

    total = len(match_data)

    for count, match in enumerate(match_data):
        message_array.append({
            'author': {
                'id': 0,
                'username': match['username'],
                'discriminator': match.get('discriminator', '0000')
            },
            'content': match['content'],
            'timestamp': datetime.strptime(match['timestamp'], '%Y-%m-%d %H:%M:%S').isoformat(),
            'attachments': [
                {
                    'filename': url.rsplit('/', 1)[1],
                    'url': url
                }
                for url in (match['attachments'].split(', ') if match.get('attachments') else [])
            ]
        })

        progress.set_progress(count + 1, total)

    return match_data
