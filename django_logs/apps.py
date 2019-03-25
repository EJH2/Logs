from django.apps import AppConfig

from decouple import config


class DjangoLogsConfig(AppConfig):
    name = 'django_logs'

    LOG_DISCORD_TOKEN = config('DISCORD_TOKEN')
