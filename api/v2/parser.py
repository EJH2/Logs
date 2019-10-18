import json
from datetime import timedelta

import celery
from django.utils import timezone

from api import tasks, utils
from api.models import Log


def create_log(content, log_type, owner, expires, privacy, guild, **kwargs) -> Log:
    """
    Create a log using specified data.
    :param content: Raw content of log.
    :type content: list
    :param log_type: Type of log, can be none if :param content is a list.
    :type log_type: Union[str, None]
    :param owner: Log owner.
    :param expires: Expiration time of log.
    :type expires: Union[int, None]
    :param privacy: Log privacy setting.
    :type privacy: str
    :param guild: Linked guild of log. Must be set if privacy setting is either guild or mods.
    :type guild: int
    :param kwargs: Extraneous data.
    """
    data = {'type': log_type, 'content': json.dumps(content, indent=4), 'owner': owner, 'privacy': privacy,
            'guild': guild}
    uuid = data['uuid'] = Log.generate_uuid(content)
    if Log.objects.filter(uuid=uuid).exists():
        return Log.objects.get(uuid=uuid)

    data['expires'] = timezone.now() + timedelta(seconds=int(expires)) if expires else None

    messages = ['{current}/{total} messages formatted... ({percent}%)', 'Saving messages... ({percent}%)']
    result = celery.chain(tasks.parse_json.s(content) | tasks.create_pages.s(uuid))()

    task_ids = utils.get_chain_tasks(result)
    data['data'] = {'tasks': utils.add_task_messages(task_ids, messages=messages), **kwargs}

    return Log.objects.update_or_create(uuid=uuid, defaults=data)[0]
