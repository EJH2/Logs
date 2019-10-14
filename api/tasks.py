from celery import shared_task
from celery_progress.backend import ProgressRecorder

from api.models import Log, Page
from api.serializers import MessageSerializer


@shared_task(bind=True)
def parse_json(self, json_data: dict):
    """
    Convert raw JSON into finished message objects.
    :param self: Task instance, supplied by Celery.
    :param json_data: Raw JSON.
    :return: Parsed data.
    """
    messages = list()
    data = dict()

    users = [dict(t) for t in {tuple(d['author'].items()) for d in json_data}]

    total = len(json_data)
    progress = ProgressRecorder(self)

    for count, msg in enumerate(json_data):
        msg = MessageSerializer(data=msg, context={'users': users})
        if msg.is_valid():
            messages.append(msg.data)

        progress.set_progress(count, total)

    def sort_chronological(value):
        return int(value.get('id') or 0) or value.get('timestamp')

    if any([messages[0].get('timestamp'), messages[0].get('id')]):
        messages.sort(key=sort_chronological)
    data['messages'] = messages

    def sort_alphabetical(value):
        return value['username']

    users.sort(key=sort_alphabetical)
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
    progress = ProgressRecorder(self)

    messages = data.pop('messages')

    batch_list = list()
    batches = range(0, len(messages), 1000)
    total = len(batches)
    for count, batch in enumerate(batches):
        progress.set_progress(count, total)
        # [[0, 1, 2...], [1000, 1001, 1002...], [2000, 2001, 2002...]...]
        batch_list.append(messages[batch:batch + 1000])  # Split messages by the 1000

    log = Log.objects.get(uuid=uuid)
    log.users = data.pop('users')
    pages = Page.objects.bulk_create([Page(log=log, messages=batch_list[i], index=i) for i in range(
        len(batch_list))])
    log.pages.set(pages)
    progress.set_progress(total, total)

    return uuid
