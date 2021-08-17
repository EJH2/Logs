import celery
import pendulum

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
    :type expires: Union[str, None]
    :param kwargs: Extraneous data.
    """
    data = {'type': log_type, 'content': content, 'uuid': Log.generate_uuid(content), 'expires': expires}

    result = celery.chain(v1_tasks.parse_text.s(log_type, content), tasks.parse_json.s())()
    data['data'] = {**result.get(), **kwargs}

    return data


def save_preview(data, owner) -> Log:
    """
    Create a log using specified data.
    :param data: Log data to create from.
    :type data: dict
    :param owner: Log owner.
    """
    data['expires'] = pendulum.parse(data['expires']) if data['expires'] else None
    data['owner'] = owner
    log_data = data.get('data')
    data['privacy'] = log_data.pop('privacy')
    data['guild'] = log_data.pop('guild')
    pages_data = {'messages': log_data.pop('messages'), 'users': log_data.pop('users')}

    result = tasks.create_pages.delay(pages_data, data['uuid'])

    data['data'] = {
        'tasks': [result.id], **log_data
    }

    return Log.objects.get_or_create(uuid=data['uuid'], defaults=data)[0]
