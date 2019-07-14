import coreapi
import coreschema
from rest_framework import schemas


def get_fields(method: str, fields: dict):
    return fields[method]


class CustomJsonSchema(schemas.AutoSchema):

    def get_manual_fields(self, path, method):
        return self._manual_fields + get_fields(method, json_fields)


json_fields = {
    'POST': [
        coreapi.Field(
            'type',
            required=False,
            location='form',
            type='integer',
            schema=coreschema.Array(
                description='Type of log',
            ),
        ),
        coreapi.Field(
            'new',
            required=False,
            location='form',
            type='boolean',
            schema=coreschema.Array(
                description='Force creation of new log'
            )
        ),
        coreapi.Field(
            'json',
            required=True,
            location='form',
            type='JSON object',
            schema=coreschema.Array(
                description='JSON object with raw message data, example found at https://mystb.in/nihubativo.json'
            )
        ),
        coreapi.Field(
            'expires',
            required=False,
            location='form',
            type='integer',
            schema=coreschema.Array(
                description='Seconds until log expiration'
            )
        ),
        coreapi.Field(
            'guild_id',
            required=False,
            location='form',
            type='integer',
            schema=coreschema.Array(
                description='Link log to a specific guild'
            )
        ),
    ]
}


class CustomViewSchema(schemas.AutoSchema):

    def get_manual_fields(self, path, method):
        return self._manual_fields + get_fields(method, view_fields)


view_fields = {
    'GET': [],
    'POST': [
        coreapi.Field(
            'type',
            required=True,
            location='form',
            type='integer',
            schema=coreschema.Array(
                description='Type of log',
            ),
        ),
        coreapi.Field(
            'new',
            required=False,
            location='form',
            type='boolean',
            schema=coreschema.Array(
                description='Force creation of new log'
            )
        ),
        coreapi.Field(
            'url',
            required=False,
            location='form',
            type='string',
            schema=coreschema.Array(
                description='URL with raw log content'
            )
        ),
        coreapi.Field(
            'content',
            required=False,
            location='form',
            type='string',
            schema=coreschema.Array(
                description='Raw log content'
            )
        ),
        coreapi.Field(
            'file',
            required=False,
            location='form',
            type='string',
            schema=coreschema.Array(
                description='File containing raw log content'
            )
        ),
        coreapi.Field(
            'expires',
            required=False,
            location='form',
            type='integer',
            schema=coreschema.Array(
                description='Seconds until log expiration'
            )
        ),
        coreapi.Field(
            'guild_id',
            required=False,
            location='form',
            type='integer',
            schema=coreschema.Array(
                description='Link log to a specific guild'
            )
        ),
    ]
}


class CustomTracebackSchema(schemas.AutoSchema):

    def get_manual_fields(self, path, method):
        return self._manual_fields + get_fields(method, traceback_fields)


traceback_fields = {
    'GET': [
        coreapi.Field(
            't',
            required=True,
            location='form',
            type='string',
            schema=coreschema.Array(
                description='List of Celery UUIDs'
            )
        ),
    ]
}
