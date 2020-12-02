import pendulum
from django.conf import settings
from itsdangerous import URLSafeSerializer
from rest_framework import serializers

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


def validate_expires(user, value):
    value = pendulum.instance(value)
    exp = {'weeks': 1}
    if user.has_perm('api.extended_expiry'):
        exp = {'months': 1}
    if user.has_perm('api.no_expiry'):
        exp = None
    if exp and value > pendulum.now().add(**exp):
        raise serializers.ValidationError(
            f'Expiry time must be an iso-8601 timestamp of a date less than '
            f'{", ".join(["{} {}".format(exp[k], k[:-1 if k.endswith("s") else k]) for k in exp])} from now!'
        )
    return value


def get_default_timestamp():
    return pendulum.now().add(minutes=30)

