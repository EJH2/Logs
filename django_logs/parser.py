import celery
from django.core import serializers

from django_logs import tasks, utils
from django_logs.models import Log, Job


class LogParser:

    @staticmethod
    def create(log_type, content, author=None, url=None, request_uri=None, *, new=True, **kwargs):
        short_code = Log.generate_short_code(content)
        filter_short = Log.objects.filter(short_code=short_code)
        if any([f.exists() for f in [Log.objects.filter(url=url, url__isnull=False).order_by('id'), filter_short,
                                     Job.objects.filter(short_code=short_code)]]) and not new:
            return short_code, False
        if filter_short.exists():
            filter_short.delete()
        author = serializers.serialize('json', [author]) if author else None
        create_data = {'url': url, 'short_code': short_code, 'log_type': log_type, 'content': content,
                       'author': author, **kwargs}
        result = celery.chain(tasks.parse.s(create_data) | tasks.parse_messages.s() | tasks.create_log.s(create_data))()
        task_ids = utils.get_chain_tasks(result)
        data = utils.add_task_messages(task_ids, messages=[
            '{current}/{total} messages parsed... ({percent}%)',
            '{current}/{total} messages formatted... ({percent}%)',
            'Saving messages... ({percent}%)'
        ])
        Job.objects.update_or_create(short_code=short_code, defaults={'data': data, 'request_uri': request_uri})
        return short_code, True
