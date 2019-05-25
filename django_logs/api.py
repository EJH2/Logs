import re
import time
from urllib.parse import urlparse

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from django_logs.consts import types, rowboat_types
from django_logs.parser import LogParser
from django_logs.utils import request_url, get_expiry


@api_view(['POST'])
@permission_classes([IsAuthenticated, ])
def api(request):
    t = time.time()
    data = request.POST
    if not all([any([any(['url', 'content']) in data, request.FILES is not None]), 'type' in data]):
        resp = {'status': 400, 'message': 'Request body must contain one of [files, url, content] and [type] '
                                          'to parse!'}
        return JsonResponse(resp, status=400)

    if data.get('type') not in types:
        resp = {'status': 400, 'message': f'Log type must be one of [{", ".join(types.keys())}]!'}
        return JsonResponse(resp, status=400)

    variant = None
    if data.get('url'):
        url = data.get('url')
        resp = request_url(url)
        if not resp:
            resp = {'status': 400, 'message': f'Connection to url "{url}" failed.'}
            return JsonResponse(resp, status=400)
        if 'text/plain' not in resp.headers['Content-Type']:
            resp = {'status': 400, 'message': f'Content-Type of "{url}" must be of type "text/plain"!'}
            return JsonResponse(resp, status=400)
        origin = ('url', url)
        variant = rowboat_types.get(urlparse(url).netloc)
        try:
            content = resp.content.decode()
        except UnicodeDecodeError:
            resp = {'status': 400, 'message': 'Request content must be of encoding utf-8!'}
            return JsonResponse(resp, status=400)
    elif data.get('content'):
        origin = 'raw'
        content = data.get('content')
    elif request.FILES:
        origin = 'file'
        with request.FILES[next(iter(request.FILES))].open() as f:
            content = f.read()
    else:  # Nothing to parse, we've given up
        resp = {'status': 400, 'message': 'Request body must contain one of [files, url, content] and [type] '
                                          'to parse!'}
        return JsonResponse(resp, status=400)

    if not content:
        resp = {'status': 400, 'message': 'Log content must not be empty!'}
        return JsonResponse(resp, status=400)

    log_type = data.get('type')
    new = data.get('new')
    match_len = len(re.findall(types[log_type], content, re.MULTILINE))
    author = request.user if request.user.is_authenticated else None
    default = 60 * 60 * 24 * 7 if author else 60 * 60 * 24
    expires = get_expiry(data, default)
    if not expires:
        resp = {'status': 400, 'message': f'Expiry time in seconds must not exceed {default}!'}
        return JsonResponse(resp, status=400)
    if match_len > 0:
        content = re.sub('\r\n', '\n', content)
        short, created = LogParser(log_type, content, origin=origin, variant=variant).create(author, expires=expires,
                                                                                             new=new)
        data = {
            'status': 201 if created else 200,
            'short': short,
            'url': f'http{"s" if request.is_secure() else ""}://{request.META["HTTP_HOST"]}/{short}',
            'created': created,
            'time': time.time() - t
        }
        return JsonResponse(data)

    resp = {'status': 400, 'message': 'Could not parse log content using specified type!'}
    return JsonResponse(resp, status=400)
