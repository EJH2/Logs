import os
from celery import Celery

from decouple import config

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_logs.settings')

redis_url = f'redis://{config("REDIS_PASSWORD")}@{config("REDIS_HOST")}:{config("REDIS_PORT")}/{config("REDIS_DB")}'

app = Celery('django_logs',
             broker=redis_url,
             backend=redis_url,
             include=['django_logs.tasks'])

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
