import time

from celery import shared_task
from celery_progress.websockets.backend import WebSocketProgressRecorder

from api.models import Log, Page
from api.serializers import MessageSerializer

# Sample author dictionary if author isn't supplied
unknown_author = {
    'id': 0,
    'username': 'Unknown User',
    'discriminator': '0000'
}


@shared_task(bind=True)
def parse_json(self, json_data: dict):
    """
    Convert raw JSON into finished message objects.
    :param self: Task instance, supplied by Celery.
    :param json_data: Raw JSON.
    :return: Parsed data.
    """
    messages = []
    bad_messages = []
    data = {}

    _users = {a['id'] or f'{a["username"]}#{a["discriminator"]}': a for a in [
        msg.get('author', unknown_author) for msg in json_data
    ]}

    total = len(json_data)
    progress = WebSocketProgressRecorder(self)

    for count, msg in enumerate(json_data):
        msg = MessageSerializer(data=msg, context={'users': _users})
        if msg.is_valid():
            messages.append(msg.data)
        else:
            bad_messages.append((msg.initial_data, msg.errors))

        progress.set_progress(count, total)

    if any([messages[0].get('timestamp'), messages[0].get('id')]):
        messages.sort(key=lambda value: int(value.get('id') or 0) or value.get('timestamp'))
    data['messages'] = messages

    users = list(_users.values())
    users.sort(key=lambda value: value['username'])
    data['users'] = users

    progress.set_progress(total, total)

    return data


@shared_task(bind=True)
def create_pages(self, data: dict, uuid: str):
    """
    Take formatted JSON log data and save it to a log.
    :param self: Task instance, supplied by Celery.
    :param data: Formatted data.
    :param uuid: Log uuid.
    :return: Log uuid.
    """
    progress = WebSocketProgressRecorder(self)

    messages = data.pop('messages')

    batch_list = []
    batches = range(0, len(messages), 1000)
    total = len(batches)
    for count, batch in enumerate(batches):
        progress.set_progress(count, total)
        # [[0, 1, 2...], [1000, 1001, 1002...], [2000, 2001, 2002...]...]
        batch_list.append(messages[batch:batch + 1000])  # Split messages by the 1000

    while not Log.objects.filter(uuid=uuid).exists():
        time.sleep(1)
    log = Log.objects.update_or_create(uuid=uuid, defaults={'users': data.pop('users')})[0]
    pages = Page.objects.bulk_create([Page(log=log, messages=batch_list[i], index=i) for i in range(
        len(batch_list))])
    log.pages.set(pages)
    progress.set_progress(total, total)

    return uuid
