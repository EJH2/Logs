import pendulum
from django.conf import settings
from itsdangerous import URLSafeSerializer
from rest_framework import serializers

signer = URLSafeSerializer(settings.SECRET_KEY)


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

