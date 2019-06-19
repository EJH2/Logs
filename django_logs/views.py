import re
from datetime import datetime
from urllib.parse import urlparse

import pytz
import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render

from django_logs.consts import rowboat_types, regexps, types
from django_logs.models import Entry, Log, Job
from django_logs.parser import LogParser
from django_logs.utils import get_expiry, request_url


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
        log = _log[0]
        if log.expires_at:
            if log.expires_at < datetime.now(pytz.UTC):
                log.delete()
                raise ObjectDoesNotExist
            if not raw:
                messages.info(request,
                              f'This log will expire on {log.expires_at.strftime("%A, %B %d, %Y at %H:%M:%S UTC")}')
        if raw:
            content = f"<pre>{log.content}</pre>"
            return HttpResponse(content)
        log_pages = log.pages.order_by('page_id')
        msgs = [msg for msgs in [p.messages for p in log_pages] for msg in msgs]
        msg_len = len(msgs)
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
        if request.session.get('cached'):
            del request.session['cached']
            messages.info(request, 'A log containing the same data was found, so we used that instead.')
        log.data['generated_at'] = log.generated_at
        log.data['messages'] = msg_page.object_list
        log.data['raw_content'] = log.content
        return render(request, 'django_logs/logs.html', context={'log_entry': Entry(log.data),
                                                                 'original_url': log.url, 'log_type': log.log_type,
                                                                 'msg_page': msg_page, 'msg_len': msg_len,
                                                                 'short': short_code})
    except ObjectDoesNotExist:
        messages.error(request, 'Log does not exist, or has expired.')
        return redirect('index')


def perks(request):
    return render(request, 'account/perks.html')


def view(request):
    if request.method == "GET":
        return render(request, 'django_logs/view.html', context={'types': types, 'whitelist': settings.LOG_WHITELIST})

    if request.method == "POST":
        url = request.POST.get('url')
        if not url:
            messages.error(request, 'You have to provide a url to parse!')
            return redirect('view')

        # Cached?
        cached = Log.objects.filter(url=url)
        if cached.exists():  # Cached
            request.session['cached'] = True
            return redirect('logs', short_code=cached.first().short_code)

        resp = request_url(url)
        if not resp:
            messages.error(request, f'Connection to url "{url}" failed. Is it a valid url?')
            return redirect('view')
        assert isinstance(resp, requests.Response)
        if 'text/plain' not in resp.headers['Content-Type']:
            messages.error(request, f'Content-Type of "{url}" must be of type "text/plain"!')
            return redirect('view')
        try:
            content = resp.content.decode()
        except UnicodeDecodeError:
            messages.error(request, 'Request content must be of encoding utf-8!')
            return redirect('view')
        if content == '':
            messages.error(request, 'You have to provide a url with text in it to parse!')
            return redirect('view')

        content = re.sub('\r\n', '\n', content)
        log_type = request.POST.get('type')
        variant = rowboat_types.get(urlparse(url).netloc)
        author = request.user if request.user.is_authenticated else None
        premium = request.user.is_staff or not bool(SocialAccount.objects.filter(user=author).first())
        req = request.build_absolute_uri()
        expires = get_expiry(request.POST, premium)
        if log_type in regexps:
            match_len = len(re.findall(regexps[log_type], content, re.MULTILINE))
            if match_len > 500:
                sec = 's' if request.is_secure() else ''
                messages.error(request, f'Logs with over 500 messages must be processed through the api, found at '
                                        f'http{sec}://{request.META["HTTP_HOST"]}/api!')
                return redirect('view')
            if match_len > 0:
                kwargs = {'expires': expires, 'origin': 'url', 'variant': variant}
                short, created = LogParser.create(log_type, content, author, url=url, request_uri=req, **kwargs)
                request.session['cached'] = not created
                return redirect('logs', short_code=short)
            messages.error(request, f'We can\'t parse that file using log type {log_type}. Maybe try another one?')
            return redirect('view')
        else:  # Mission failed, we'll get em next time
            messages.error(request, f'Log type {log_type} doesn\'t exist. Maybe try another one?')
            return redirect('view')


def handle404(request, exception):
    messages.error(request, f'Error: {exception}')
    return redirect('index')


def handle500(request):
    messages.error(request, 'Something broke, please contact EJH2#0330 on Discord about this issue!')
    return redirect('index')
