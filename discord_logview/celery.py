import os
import sys
from datetime import datetime

import pytz
from celery import Celery
from decouple import config

if config('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    init_kwargs = {
        'dsn': config('SENTRY_DSN'),
        'integrations': [DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
        'send_default_pii': True
    }
    if sys.platform == 'win32':
        from raven.transport.eventlet import EventletHTTPTransport

        init_kwargs['transport'] = EventletHTTPTransport
    sentry_sdk.init(**init_kwargs)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'discord_logview.settings')

redis_url = f'redis://{config("REDIS_PASSWORD")}@{config("REDIS_HOST")}:{config("REDIS_PORT")}/{config("REDIS_DB")}'

app = Celery('discord_logview',
             broker=redis_url,
             backend=redis_url,
             include=[
                 'api.tasks',
                 'api.v1.tasks',
             ])

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60 * 10, clean_expired.s(), name='clean expired logs')


@app.task
def clean_expired():
    from api.models import Log
    logs = Log.objects.filter(expires_at__isnull=False, expires_at__lt=datetime.now(pytz.UTC))
    logs.delete()
