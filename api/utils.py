from celery.result import AsyncResult
from django.conf import settings
from itsdangerous import URLSafeSerializer
from rest_framework import serializers

from api.consts import expiry_times


signer = URLSafeSerializer(settings.SECRET_KEY)


def add_task_messages(task_list: list, messages: list = None) -> list:
    """
    Add messages to tasks for use in Job template.
    :param task_list: List of task IDs.
    :param messages: List of messages to be connected to tasks.
    """
    if not messages:
        messages = [''] * len(task_list)
    if len(messages) == len(task_list):
        for count, task in enumerate(task_list):
            task_list[count] = (task, messages[count])
    return task_list


def get_chain_tasks(node) -> list:
    """
    Get task IDs from a Redis job.
    :param node: Redis job.
    """
    id_chain = []
    while node.parent:
        id_chain.insert(0, node.id)
        node = node.parent
    id_chain.insert(0, node.id)
    return id_chain


def forget_tasks(log):
    task_list = log.data['tasks']
    del log.data['tasks']
    tasks = [task[0] for task in task_list]
    for task_id in tasks:
        task = AsyncResult(id=task_id)
        task.forget()
    log.save()


def validate_expires(user, value):
    exp = list(expiry_times.keys())[:5]
    if user.has_perm('log.extended_expiry'):
        exp = list(expiry_times.keys())[:7]
    if user.has_perm('log.no_expiry'):
        exp = expiry_times
    if value.lower() not in exp:
        raise serializers.ValidationError(f'Expiry time must be one of {", ".join(exp)}!')
    return value

