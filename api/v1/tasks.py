from celery import shared_task
from celery_progress.backend import ProgressRecorder

from api.consts import rowboat_types
from api.v1 import handlers


@shared_task(bind=True)
def parse_text(self, log_type: str, content: str):
    """
    Convert raw log content into usable data.
    :param self: Task instance, supplied by Celery.
    :param log_type: Log type.
    :param content: Log content.
    :return: Parsed data.
    """
    if log_type in rowboat_types:
        log_type = 'rowboat'
    parser = getattr(handlers, log_type)
    message_array = parser(content, ProgressRecorder(self))
    return message_array
