import re
from datetime import datetime
from urllib.parse import urlparse

import pytz
import requests
from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from django_logs import utils
from django_logs.consts import rowboat_types, types
from django_logs.models import Entry, Log, Job
from django_logs.parser import LogParser
from django_logs.utils import request_url, get_expiry


# Create your views here.
def index(request):
    return render(request, 'django_logs/index.html', context={'iso': datetime.now(pytz.UTC).isoformat()})


def logs(request, short_code: str, raw=False):
    try:
        processing = Job.objects.filter(short_code=short_code)
        _log = Log.objects.filter(short_code=short_code)
        if not _log.exists():
            if processing.exists():
                ids = list(enumerate(processing[0].data['tasks']))
                req = processing[0].request_uri
                return render(request, 'django_logs/loading.html', context={'task_ids': ids, 'request_uri': req,
                                                                            'iso': datetime.now(pytz.UTC).isoformat()})
            raise ObjectDoesNotExist
        utils.forget_tasks(processing)
        log = _log[0]
        if log.expires_at < datetime.now(pytz.UTC):
            log.delete()
            raise ObjectDoesNotExist
        if raw:
            content = f"<pre>{log.content}</pre>"
            return HttpResponse(content)
        chunked = False
        msg_page = None
        log_pages = log.pages.order_by('page_id')
        msgs = [msg for msgs in [p.messages for p in log_pages] for msg in msgs]
        msg_len = len(msgs)
        if msg_len > 100:
            chunked = True
            page = request.GET.get('page')
            if not request.is_ajax() and page:
                return redirect('logs', short_code=short_code)

            paginator = Paginator(msgs, 100)
            try:
                msg_page = paginator.page(page)
            except PageNotAnInteger:
                msg_page = paginator.page(1)
            except EmptyPage:
                msg_page = paginator.page(paginator.num_pages)
            log.messages = msg_page.object_list
        if request.session.get('cached'):
            del request.session['cached']
            messages.info(request, 'A log containing the same data was found, so we used that instead.')
        log.data['generated_at'] = log.generated_at
        log.data['messages'] = msgs
        log.data['raw_content'] = log.content
        return render(request, 'django_logs/logs.html', context={'log_entry': Entry(log.data),
                                                                 'original_url': log.url, 'log_type': log.log_type,
                                                                 'chunked': chunked, 'msg_page': msg_page,
                                                                 'msg_len': msg_len, 'short': short_code})
    except ObjectDoesNotExist:
        messages.error(request, 'Log does not exist, or has expired.')
        return redirect('index')


@user_passes_test(lambda u: u.is_superuser)
def traceback(request):
    t = request.GET.get('t')
    tasks = t.split(',')
    gathered = []
    for task in tasks:
        t = AsyncResult(id=task)
        gathered.append({'id': t.id, 'status': t.status, 'result': t.result if not
        isinstance(t.result, Exception) else None, 'traceback': t.traceback})
    return JsonResponse(gathered, safe=False)


def perks(request):
    return render(request, 'account/perks.html')


def view(request):
    url = request.GET.get('url')
    if not url:
        messages.error(request, 'You have to provide a url to parse!')
        return redirect('index')

    # Cached?
    cached = Log.objects.filter(url=url)
    if cached.exists() and not request.GET.get('new'):  # Cached, and user wants from cache
        request.session['cached'] = True
        return redirect('logs', short_code=cached[0].short_code.split('-')[0])

    resp = request_url(url)
    if not resp:
        messages.error(request, f'Connection to url "{url}" failed. Is it a valid url?')
        return redirect('index')
    assert isinstance(resp, requests.Response)
    if 'text/plain' not in resp.headers['Content-Type']:
        messages.error(request, f'Content-Type of "{url}" must be of type "text/plain"!')
        return redirect('index')
    try:
        content = resp.content.decode()
    except UnicodeDecodeError:
        messages.error(request, 'Request content must be of encoding utf-8!')
        return redirect('index')
    if content == '':
        messages.error(request, 'You have to provide a url with text in it to parse!')
        return redirect('index')

    content = re.sub('\r\n', '\n', content)
    log_type = request.GET.get('type')
    variant = rowboat_types.get(urlparse(url).netloc)
    author = request.user if request.user.is_authenticated else None
    req = request.build_absolute_uri()
    default = 60 * 60 * 24 * 7 if author else 60 * 60 * 24
    expires = get_expiry(request.GET, default)
    if not expires:
        messages.error(request, f'Expiry time in seconds must not exceed {default}!')
        return redirect('index')
    if log_type and log_type in types:
        match_len = len(re.findall(types[log_type], content, re.MULTILINE))
        if match_len > 0:
            short, created = LogParser(log_type, content, origin=('url', url), variant=variant, request_uri=req).create(
                author, expires=expires, new=True)
            request.session['cached'] = not created
            return redirect('logs', short_code=short)
        messages.error(request, f'We can\'t seem to parse that file using log type {log_type}. Maybe try another one?')
        return redirect('index')
    if log_type and log_type not in types:
        messages.error(request, f'We can\'t seem to parse that file using log type {log_type}. Maybe try another one?')
        return redirect('index')
    for log_type in types.keys():  # Try all log types
        match_len = len(re.findall(types[log_type], content, re.MULTILINE))
        if match_len > 500:
            sec = 's' if request.is_secure() else ''
            messages.error(request, f'Logs with over 500 messages must be processed through the api, found at '
                                    f'http{sec}://{request.META["HTTP_HOST"]}/api!')
            return redirect('index')
        if match_len > 0:
            short, created = LogParser(log_type, content, origin=('url', url), variant=variant, request_uri=req).create(
                author, expires=expires, new=True)
            request.session['cached'] = not created
            return redirect('logs', short_code=short)

    # Mission failed, we'll get em next time
    messages.error(request, 'We can\'t seem to parse that file. Are you sure it\'s a valid log type?')
    return redirect('index')


def handle404(request, exception):
    messages.error(request, 'Page not found.')
    return redirect('index')


def handle500(request):
    messages.error(request, 'Something broke, please contact EJH2#0330 on Discord about this issue!')
    return redirect('index')
