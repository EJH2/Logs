from datetime import timedelta

import celery
import dateutil.parser
from django.utils import timezone

from api import tasks, utils
from api.models import Log
from api.v1 import tasks as v1_tasks


def create_preview(content, log_type, expires, **kwargs) -> dict:
    """
    Create a log using specified data.
    :param content: Raw content of log.
    :type content: str
    :param log_type: Type of log, can be none if :param content is a list.
    :type log_type: Union[str, None]
    :param expires: Expiration time of log.
    :type expires: Union[int, None]
    :param kwargs: Extraneous data.
    """
    data = {'type': log_type, 'content': content, 'uuid': Log.generate_uuid(content),
            'expires': (timezone.now() + timedelta(seconds=int(expires))).isoformat() if expires else None}

    result = celery.chain(v1_tasks.parse_text.s(log_type, content), tasks.parse_json.s())()
    data['data'] = result.get()

    return data


def save_preview(data, owner) -> Log:
    """
    Create a log using specified data.
    :param data: Log data to create from.
    :type data: dict
    :param owner: Log owner.
    """
    data['expires'] = dateutil.parser.parse(data['expires']) if data['expires'] else None
    data['owner'] = owner
    log_data = data.pop('data')

    result = tasks.create_pages.delay(log_data, data['uuid'])

    data['data'] = {'tasks': utils.add_task_messages([result.id], messages=['Saving messages... ({percent}%)'])}

    return Log.objects.create(**data)
