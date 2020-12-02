import json
import os
import subprocess

import pendulum

import redis
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
        'send_default_pii': True,
        'release': subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode()
    }
    sentry_sdk.init(**init_kwargs)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'discord_logview.settings')

redis_url = f'redis://{config("REDIS_PASSWORD")}@{config("REDIS_HOST")}:{config("REDIS_PORT")}/{config("REDIS_DB")}'
redis_app = redis.Redis.from_url(redis_url)

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


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60 * 60, clean_expired_logs.s(), name='clean expired logs')
    sender.add_periodic_task(60 * 60, clean_old_tasks.s(), name='clean old tasks')


@app.task
def clean_old_tasks():
    for key in redis_app.keys('celery-task-meta-*'):
        data = json.loads(redis_app.get(key))
        if data['status'] == 'SUCCESS' and data['date_done'] < pendulum.now().add(minutes=5).isoformat():
            redis_app.delete(key)


@app.task
def clean_expired_logs():
    from api.models import Log
    logs = Log.objects.filter(expires__isnull=False, expires__lt=pendulum.now())
    logs.delete()
