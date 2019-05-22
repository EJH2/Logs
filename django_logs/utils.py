import ast
import json
import re

import requests
from celery.result import AsyncResult
from django.db.models import QuerySet

from django_logs.consts import attachment_re
from django_logs.models import Log


def update_db(objects, create_data, messages):
    first = objects[0]
    assert isinstance(first, Log)

    # These messages don't need chunking
    if len(messages) <= 1000 and first.chunked is False:
        return objects.update(**create_data, messages=messages)
    if len(messages) <= 1000 and first.chunked is True:
        objects.delete()
        return Log.objects.create(**create_data, messages=messages)

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
    new_first = Log(**create_data, short_code=short_code, messages=batch_list[0])
    create_data['data'] = None
    create_data['content'] = None
    new_rest = (Log(**create_data, short_code=f'{short_code}-{i}', messages=batch_list[i]) for i in range(
        1, len(batch_list)))
    new_objects = [new_first, *new_rest]
    logs = Log.objects.bulk_create(new_objects)
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


def get_expiry(data: dict, default: int):
    expires = data.get('expires', 60 * 60 * 12)
    if isinstance(expires, str):
        expires = int(expires) if expires.isdigit() else default
    if expires > default:
        return None
    return expires


def get_chain_tasks(node):
    id_chain = []
    while node.parent:
        id_chain.insert(0, node.id)
        node = node.parent
    id_chain.insert(0, node.id)
    return id_chain


def add_task_messages(task_list: list, messages: list = None):
    if not messages:
        messages = [''] * len(task_list)
    if len(messages) == len(task_list):
        for count, task in enumerate(task_list):
            task_list[count] = (task, messages[count])
    return {'tasks': task_list}


def forget_tasks(jobs: QuerySet):
    tasks = [task[0] for task in [subtasklist for bigtasklist in [job.data for job in jobs] for
                                  subtasklist in bigtasklist]]
    for task_id in tasks:
        task = AsyncResult(id=task_id)
        task.forget()
    jobs.delete()
