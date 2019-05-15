import ast
import json
import re

import requests

from django_logs.consts import attachment_re
from django_logs.models import LogRoute


def update_db(objects, create_data, messages):
    first = objects[0]
    assert isinstance(first, LogRoute)

    # These messages don't need chunking
    if len(messages) <= 1000 and first.chunked is False:
        return objects.update(**create_data, messages=messages)
    if len(messages) <= 1000 and first.chunked is True:
        objects.delete()
        return LogRoute.objects.create(**create_data, messages=messages)

    # These messages do
    objects.delete()  # Wipe the row(s) so no old info is left over
    create_chunked_logs(**create_data, messages=messages)


def create_chunked_logs(**create_data):
    batch_list = list()
    short_code = create_data.pop('short_code')
    messages = create_data.pop('messages')
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


def get_attach_info(attachments: list):
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


def get_embed_info(embeds: str):
    try:
        return json.loads(embeds)
    except json.decoder.JSONDecodeError:
        try:
            return ast.literal_eval(embeds)  # I'M SORRY
        except AttributeError:
            return dict()


def request_url(url: str):
    try:
        try:
            resp = requests.get(url, stream=True)
        except requests.exceptions.MissingSchema:
            resp = requests.get('https://' + url, stream=True)
    except requests.exceptions.ConnectionError:
        resp = None
    return resp


def get_expiry(data, default):
    expires = data.get('expires', 60 * 60 * 12)
    if isinstance(expires, str):
        expires = int(expires) if expires.isdigit() else default
    if expires > default:
        return None
    return expires
