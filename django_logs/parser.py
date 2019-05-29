import celery
from django.core import serializers

from django_logs.models import Log, Job
from django_logs import tasks, utils


class LogParser:

    def __init__(self, log_type, content, origin='url', url=None, variant=None, request_uri=None):
        self.log_type = log_type
        self.variant = variant
        self.content = content

        self.request_uri = request_uri

        self.url = url
        self.origin = origin

    def create(self, author=None, *, expires=None, new=True):
        short_code = Log.generate_short_code(self.content)
        filter_short = Log.objects.filter(short_code=short_code)
        if any([f.exists() for f in [Log.objects.filter(url=self.url, url__isnull=False).order_by('id'), filter_short,
                                     Job.objects.filter(short_code=short_code)]]) and not new:
            return short_code, False
        if filter_short.exists():
            filter_short.delete()
        author = serializers.serialize('json', [author]) if author else None
        create_data = {'origin': self.origin, 'url': self.url, 'short_code': short_code, 'log_type': self.log_type,
                       'variant': self.variant, 'content': self.content, 'expires': expires, 'author': author}
        result = celery.chain(tasks.parse.s(create_data) | tasks.parse_messages.s() | tasks.create_log.s(create_data))()
        task_ids = utils.get_chain_tasks(result)
        data = utils.add_task_messages(task_ids, messages=[
            '{current}/{total} messages parsed... ({percent}%)',
            '{current}/{total} messages formatted... ({percent}%)',
            'Saving messages... ({percent}%)'
        ])
        Job.objects.update_or_create(short_code=short_code, defaults={'data': data, 'request_uri': self.request_uri})
        return short_code, True
