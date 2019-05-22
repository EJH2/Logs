import celery
from django.core import serializers

from django_logs.models import Log, Job
from django_logs import tasks, utils


class LogParser:

    def __init__(self, log_type, content, origin=None, variant=None, request_uri=None):
        self.log_type = log_type
        self.variant = variant
        self.content = content

        self.request_uri = request_uri

        self.url = None
        self.origin = origin
        if isinstance(origin, tuple):
            self.url = origin[1]
            self.origin = 'url'

    def create(self, author=None, *, expires=None, new=False):
        short_code = Log.generate_short_code(self.content)
        filter_url = Log.objects.filter(url=self.url).filter(url__isnull=False).order_by('id')
        filter_short = Log.objects.filter(short_code__startswith=short_code)
        filter_job = Job.objects.filter(short_code=short_code)
        if any([filter_url.exists(), filter_short.exists(), filter_job.exists()]) and not new:
            return short_code, False
        if filter_short.exists():
            filter_short.delete()
        if author:
            author = serializers.serialize('json', [author])
        create_data = {'origin': self.origin, 'url': self.url, 'short_code': short_code, 'log_type': self.log_type,
                       'variant': self.variant, 'content': self.content, 'expires': expires, 'author': author}
        extras = {'filter_url': list(filter_url)}
        result = celery.chain(tasks.parse.s(create_data) | tasks.parse_messages.s() | tasks.create_log.s(
            extras, create_data))()
        task_ids = utils.get_chain_tasks(result)
        msgs = [
            '{current}/{total} messages parsed... ({percent}%)',
            '{current}/{total} messages formatted... ({percent}%)',
            'Saving messages... ({percent}%)'
        ]
        data = utils.add_task_messages(task_ids, msgs)
        job = Job.objects.filter(short_code=short_code)
        if job.exists():
            job[0].data = data
            job[0].save()
        else:
            Job.objects.create(short_code=short_code, data=data, request_uri=self.request_uri)
        return short_code, True
