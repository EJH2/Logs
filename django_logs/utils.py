import ast
import json
import re

import requests
from celery.result import AsyncResult
from django.db.models import QuerySet

from django_logs.consts import attachment_re
from django_logs.models import Log, Page


def create_log_entry(**create_data):
    batch_list = list()
    messages = create_data.pop('messages')
    short_code = create_data.pop('short_code')
    for batch in range(0, len(messages), 1000):
        # [[0, 1, 2...], [1000, 1001, 1002...], [2000, 2001, 2002...]...]
        batch_list.append(messages[batch:batch + 1000])  # Split messages by the 1000

    create_data['chunked'] = len(batch_list) > 1
    log, _ = Log.objects.update_or_create(short_code=short_code, defaults=create_data)
    pages = Page.objects.bulk_create([Page(log=log, messages=batch_list[i], page_id=i) for i in range(
        len(batch_list))])
    log.pages.set(pages)
    return log


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
            resp = requests.get(url, stream=True, timeout=10)
        except requests.exceptions.MissingSchema:
            resp = requests.get('https://' + url, stream=True, timeout=10)
        if resp.status_code != 200:
            resp = None
    except requests.exceptions.ConnectionError:
        resp = None
    return resp


def get_expiry(data: dict):
    default = 60 * 60 * 24 * 7 * 2  # 2 week default
    expires = data.get('expires', default)
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
    tasks = [task[0] for task in [sublist for biglist in [job.data for job in jobs] for sublist in biglist]]
    for task_id in tasks:
        task = AsyncResult(id=task_id)
        task.forget()
    jobs.delete()
