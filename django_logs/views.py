import pytz
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from django_logs import home
from django_logs.models import LogEntry
from django_logs.parser import *

types = {'capnbot': capnbot_re, 'rowboat': rowboat_re, 'rosalina_bottings': rosalina_bottings_re,
             'giraffeduck': giraffeduck_re, 'auttaja': auttaja_re, 'logger': logger_re, 'sajuukbot': sajuukbot_re,
             'spectra': spectra_re, 'gearboat': gearboat_re}


def _request_url(url: str):
    try:
        try:
            resp = requests.get(url, stream=True)
        except requests.exceptions.MissingSchema:
            resp = requests.get('https://' + url, stream=True)
    except requests.exceptions.ConnectionError:
        resp = None
    return resp


# Create your views here.
def index(request):
    home.content = home.content.replace('0000-00-00 00:00:00', datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'))
    data, _ = LogParser('giraffeduck').parse(home.content)
    data['type'] = None
    data['generated_at'] = datetime.now()
    data['raw_content'] = home.content
    return render(request, 'django_logs/logs.html', context={'log_entry': LogEntry(data), 'log_type': None,
                                                             'msg_len': 1})


def logs(request, short_code: str, raw=False):
    try:
        short_code = short_code.split('-')[0]
        _log = LogRoute.objects.filter(short_code__startswith=short_code)
        if not _log.exists():
            raise ObjectDoesNotExist
        log = _log[0]
        chunked = False
        msg_page = None
        msg_len = len(log.messages)
        if _log.count() > 1:
            chunked = True
            page = request.GET.get('page', None)
            if not request.is_ajax() and page:
                return redirect('logs', short_code=short_code)

            msgs = [msg for msgs in [_l.messages for _l in _log.order_by('id')] for msg in msgs]
            msg_len = len(msgs)
            paginator = Paginator(msgs, 100)
            try:
                msg_page = paginator.page(page)
            except PageNotAnInteger:
                msg_page = paginator.page(1)
            except EmptyPage:
                msg_page = paginator.page(paginator.num_pages)
            log.messages = msg_page.object_list
        if raw:
            content = f"<pre>{log.content}</pre>"
            return HttpResponse(content)
        if request.session.get('cached', None):
            del request.session['cached']
            messages.warning(request, 'A log containing the same data was found, so we used that instead.')
        log.data['generated_at'] = log.generated_at
        log.data['messages'] = log.messages
        log.data['raw_content'] = log.content
        return render(request, 'django_logs/logs.html', context={'log_entry': LogEntry(log.data),
                                                                 'original_url': log.url, 'log_type': log.log_type,
                                                                 'chunked': chunked, 'msg_page': msg_page,
                                                                 'msg_len': msg_len, 'short': short_code})
    except ObjectDoesNotExist:
        messages.error(request, 'Log not found.')
        return redirect('index')


def api(request):
    if not request.method == 'POST':
        resp = {'status': 405, 'message': 'This endpoint only accepts POST requests!'}
        return JsonResponse(resp, status=405)

    data = request.POST
    if not all([any([any(['url', 'content']) in data, request.FILES is not None]), 'type' in data]):
        resp = {'status': 400, 'message': 'Request body must contain one of [files, url, content] and [type] '
                                          'to parse!'}
        return JsonResponse(resp, status=400)

    if data.get('type') not in types:
        resp = {'status': 400, 'message': f'Log type must be one of [{", ".join(types.keys())}]!'}
        return JsonResponse(resp, status=400)

    if data.get('url'):
        url = data.get('url')
        resp = _request_url(url)
        if not resp:
            resp = {'status': 400, 'message': f'Connection to url "{url}" failed.'}
            return JsonResponse(resp, status=400)
        if 'text/plain' not in resp.headers['Content-Type']:
            resp = {'status': 400, 'message': f'Content-Type of "{url}" must be of type "text/plain"!'}
            return JsonResponse(resp, status=400)
        origin = ('url', url)
        content = resp.content.decode()
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
    match_len = len(re.findall(types[log_type], content, re.MULTILINE))
    if match_len > 0:
        content = re.sub('\r\n', '\n', content)
        short, created = LogParser(log_type=log_type).create(content, origin)
        sec = 's' if request.is_secure() else ''
        data = {
            'status': 200,
            'short': short,
            'url': f'http{sec}://{request.META["HTTP_HOST"]}/{short}',
            'created': created
        }
        return JsonResponse(data)

    resp = {'status': 400, 'message': 'Could not parse log content using specified type!'}
    return JsonResponse(resp, status=400)


def view(request):
    url = request.GET.get('url', None)
    if not url:
        messages.error(request, 'You have to provide a url to parse!')
        return redirect('index')

    # Cached?
    cached = LogRoute.objects.filter(url=url)
    if cached.exists() and not request.GET.get('new', None):  # Cached, and user wants from cache
        request.session['cached'] = True
        return redirect('logs', short_code=cached[0].short_code.split('-')[0])

    resp = _request_url(url)
    if not resp:
        messages.error(request, f'Connection to url "{url}" failed. Is it a valid url?')
        return redirect('index')
    assert isinstance(resp, requests.Response)
    if 'text/plain' not in resp.headers['Content-Type']:
        messages.error(request, f'Content-Type of "{url}" must be of type "text/plain"!')
        return redirect('index')
    content = resp.content.decode()
    if content == '':
        messages.error(request, 'You have to provide a url with text in it to parse!')
        return redirect('index')

    content = re.sub('\r\n', '\n', content)
    for log_type in types.keys():  # Try all log types
        match_len = len(re.findall(types[log_type], content, re.MULTILINE))
        if match_len > 500:
            sec = 's' if request.is_secure() else ''
            messages.error(request, f'Logs with over 500 messages must be processed through the api, found at '
                                    f'http{sec}://{request.META["HTTP_HOST"]}/api!')
            return redirect('index')
        if match_len > 0:
            print(match_len)
            short, created = LogParser(log_type=log_type).create(content, ('url', url), new=True)
            request.session['cached'] = not created
            return redirect('logs', short_code=short)

    # Mission failed, we'll get em next time
    messages.error(request, 'We can\'t seem to parse that file. Are you sure it\'s a valid log type?')
    return redirect('index')


def handle404(request):
    messages.error(request, 'Log not found.')
    return redirect('index')


def handle500(request):
    messages.error(request, 'Something broke, please contact EJH2#0330 on Discord about this issue!')
    return redirect('index')
