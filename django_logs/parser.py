# import celery

from django_logs.models import LogRoute
from django_logs import tasks


class LogParser:

    def __init__(self, log_type, content, origin=None, variant=None):
        self.log_type = log_type
        self.variant = variant
        self.content = content

        self.url = None
        self.origin = origin
        if isinstance(origin, tuple):
            self.url = origin[1]
            self.origin = 'url'

    def create(self, author=None, *, expires=None, new=False):
        short_code = LogRoute.generate_short_code(self.content)
        filter_url = LogRoute.objects.filter(url=self.url).filter(url__isnull=False).order_by('id')
        filter_short = LogRoute.objects.filter(short_code__startswith=short_code)
        if any([filter_url.exists(), filter_short.exists()]) and not new:
            return short_code, False
        if filter_short.exists():
            filter_short.delete()
        create_data = {'origin': self.origin, 'url': self.url, 'short_code': short_code, 'log_type': self.log_type,
                       'variant': self.variant, 'content': self.content, 'filter_url': filter_url, 'expires': expires,
                       'author': author}
        data, match_data, create_data = tasks.parse(**create_data)
        data = tasks.parse_messages(data, match_data)
        created = tasks.create_log(data, **create_data)
        # celery.chain(tasks.parse(**create_data) | tasks.parse_messages() | tasks.create_log(**create_data))
        return short_code, created
