import json
import re
import time
from urllib.parse import urlparse

from allauth.socialaccount.models import SocialAccount
from celery.result import AsyncResult
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api import schema
from api.serializers import LogSerializer
from django_logs.auth import filter_query, IsWhitelisted
from django_logs.consts import regexps, rowboat_types
from django_logs.models import Log
from django_logs.parser import LogParser
from django_logs.utils import get_expiry, request_url


# Create your views here.
class JsonView(APIView):
    """
    post:
    Create a log based on raw json for the messages. The request parameters are the same as the other post request.
    """

    permission_classes = [IsAuthenticated, IsWhitelisted]
    schema = schema.CustomJsonSchema()

    @staticmethod
    def post(request):
        t = time.time()
        data = request.POST
        if 'json' not in data:
            resp = {'detail': 'Request body must [json] to parse!'}
            return Response(resp, status=400)

        if data.get('type') and data.get('type') not in regexps:
            resp = {'detail': f'Log type must be one of [{", ".join(regexps.keys())}], or omitted!'}
            return Response(resp, status=400)

        try:
            js = json.loads(data['json'])
        except json.decoder.JSONDecodeError:
            resp = {'detail': 'Malformed JSON received!'}
            return Response(resp, status=400)

        if not js:
            resp = {'detail': 'JSON must not be empty!'}
            return Response(resp, status=400)

        if not isinstance(js, list):
            resp = {'detail': 'JSON must be a list of messages!'}
            return Response(resp, status=400)

        log_type = data.get('type')
        author = request.user if request.user.is_authenticated else None
        premium = request.user.is_staff or not bool(SocialAccount.objects.filter(user=author).first())
        expires = get_expiry(data, premium)

        kwargs = {'expires': expires, 'guild_id': data.get('guild_id')}
        short, created = LogParser.parse(js, log_type, author, new=data.get('new'), **kwargs)
        data = {
            'short': short,
            'url': f'http{"s" if request.is_secure() else ""}://{request.META["HTTP_HOST"]}/{short}',
            'created': created,
            'expires': expires,
            'time': time.time() - t
        }
        return Response(data, status=201 if created else 200)


class LogView(APIView):
    """
    get:
    Return a list of logs currently owned by the user, or are linked to a guild where a user has elevated permissions.

    post:
    Creates a new log.

    Request body must contain either `url`, `content`, or `file`.

    The default (and maximum) value for `expires` this is one week, or two weeks for premium users.

    Specifying `guild_id` will link the log to a guild allowing anyone with either Manage Guild, Manage Messages, or
    Administrator to get information or delete it.
    """

    permission_classes = [IsAuthenticated, IsWhitelisted]
    schema = schema.CustomViewSchema()

    @staticmethod
    @action(schema=schema, detail=True, methods=['get'])
    def get(request):
        logs = filter_query(request, Log.objects.all())
        serializer = LogSerializer(logs, many=True)
        return Response(serializer.data or {'detail': 'Not found.'})

    @staticmethod
    def post(request, **kwargs):
        if kwargs:
            resp = {'detail': 'POSTing to a log is not allowed!'}
            return Response(resp, status=405)
        t = time.time()
        data = request.POST
        if not all([any([any(['url', 'content']) in data, request.FILES is not None]), 'type' in data]):
            resp = {'detail': 'Request body must contain one of [files, url, content] and [type] to parse!'}
            return Response(resp, status=400)

        if data.get('type') not in regexps:
            resp = {'detail': f'Log type must be one of [{", ".join(regexps.keys())}]!'}
            return Response(resp, status=400)

        variant = None
        url = None
        if data.get('url'):
            url = data.get('url')
            resp = request_url(url)
            if not resp:
                resp = {'detail': f'Connection to url "{url}" failed.'}
                return Response(resp, status=400)

            if 'text/plain' not in resp.headers['Content-Type']:
                resp = {'detail': f'Content-Type of "{url}" must be of type "text/plain"!'}
                return Response(resp, status=400)

            origin = 'url'
            variant = rowboat_types.get(urlparse(url).netloc)
            try:
                content = resp.content.decode()
            except UnicodeDecodeError:
                resp = {'detail': 'Request content must be of encoding utf-8!'}
                return Response(resp, status=400)

        elif data.get('content'):
            origin = 'raw'
            content = data.get('content')
        elif request.FILES:
            origin = 'file'
            with request.FILES[next(iter(request.FILES))].open() as f:
                content = f.read()
                if isinstance(content, bytes):
                    content = content.decode()
        else:  # Nothing to parse, we've given up
            resp = {'detail': 'Request body must contain one of [files, url, content] and [type] to parse!'}
            return Response(resp, status=400)

        if not content:
            resp = {'detail': 'Log content must not be empty!'}
            return Response(resp, status=400)

        log_type = data.get('type')
        match_len = len(re.findall(regexps[log_type], content, re.MULTILINE))
        author = request.user if request.user.is_authenticated else None
        premium = request.user.is_staff or not bool(SocialAccount.objects.filter(user=author).first())
        expires = get_expiry(data, premium)

        if match_len > 0:
            content = re.sub('\r\n', '\n', content)
            kwargs = {'expires': expires, 'origin': origin, 'variant': variant, 'guild_id': data.get('guild_id')}
            short, created = LogParser.create(log_type, content, author, url=url, new=data.get('new'), **kwargs)
            data = {
                'short': short,
                'url': f'http{"s" if request.is_secure() else ""}://{request.META["HTTP_HOST"]}/{short}',
                'created': created,
                'expires': expires,
                'time': time.time() - t
            }
            return Response(data, status=201 if created else 200)

        resp = {'detail': 'Could not parse log content using specified type!'}
        return Response(resp, status=400)


class LogRead(APIView):
    """
    get:
    Grabs data for a specific log.

    delete:
    Deletes a log, specified with `short_code`.
    """

    permission_classes = [IsAuthenticated, ]

    @staticmethod
    def get(request, short_code):
        log = get_object_or_404(filter_query(request, Log.objects.all()), short_code=short_code)
        serializer = LogSerializer(log)
        return Response(serializer.data)

    @staticmethod
    def delete(request, short_code):
        log = get_object_or_404(filter_query(request, Log.objects.all()), short_code=short_code)
        log.delete()
        return Response({'detail': f'Log {short_code} has been deleted.'})


class GetToken(APIView):
    """
    get:
    Generates a token for a user account.
    """

    permission_classes = [IsAuthenticated, ]
    schema = None

    @staticmethod
    def get(request):
        if not request.user.is_authenticated or not request.is_ajax():
            return Response({'detail': 'Unauthorized.'}, status=401)
        token, created = Token.objects.update_or_create(user=request.user)
        return Response({'token': token.key}, status=201 if created else 200)


class GetTraceback(APIView):
    """
    get:
    Gets data corresponding to a set of Celery keys.
    """

    permission_classes = [IsAdminUser, ]
    schema = schema.CustomTracebackSchema()

    @staticmethod
    def get(request):
        t = request.data.get('t')
        tasks = t.split(',')
        gathered = []
        for task in tasks:
            t = AsyncResult(id=task)
            gathered.append({'id': t.id, 'status': t.status, 'result': t.result if not isinstance(
                t.result, Exception) else None, 'traceback': t.traceback})
        return Response(gathered)
