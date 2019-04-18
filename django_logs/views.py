import pytz
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
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
            resp = requests.get(url)
        except requests.exceptions.MissingSchema:
            resp = requests.get('https://' + url)
    except requests.exceptions.ConnectionError:
        resp = None
    return resp


# Create your views here.
def index(request):
    home.content = home.content.replace('0000-00-00 00:00:00', datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'))
    data, _ = LogParser('giraffeduck').parse(home.content)
    data['type'] = None
    data['generated_at'] = datetime.now()
    return render(request, 'django_logs/logs.html', context={'log_entry': LogEntry(data), 'log_type': None})


def logs(request, short_code, raw=False):
    try:
        log = LogRoute.objects.get(short_code=short_code)
        if raw:
            content = f"<pre>{log.data['raw_content']}</pre>"
            return HttpResponse(content)
        if request.session.get('cached', None):
            del request.session['cached']
            messages.warning(request, 'A log containing the same data was found, so we used that instead.')
        log.data['generated_at'] = log.generated_at
        return render(request, 'django_logs/logs.html', context={'log_entry': LogEntry(log.data),
                                                                 'original_url': log.url,
                                                                 'log_type': log.log_type})
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

    url = None

    if data.get('url'):
        url = data.get('url')
        resp = _request_url(url)
        if not resp:
            resp = {'status': 400, 'message': f'Connection to url "{url}" failed.'}
            return JsonResponse(resp, status=400)
        else:
            content = resp.content.decode()
    elif data.get('content'):
        content = data.get('content')
    elif request.FILES:
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
        short, created = LogParser(log_type=log_type).create(content, url)
        data = {
            'status': 200,
            'short': short,
            'url': f'{request.META["HTTP_HOST"]}/{short}',
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
    cached = LogRoute.objects.filter(url=url).exists()
    if cached and not request.GET.get('new', None):  # Cached, and user wants from cache
        request.session['cached'] = True
        return redirect('logs', short_code=LogRoute.objects.get(url=url).short_code)

    resp = _request_url(url)
    if not resp:
        messages.error(request, f'Connection to url "{url}" failed. Is it a valid url?')
        return redirect('index')
    assert isinstance(resp, requests.Response)
    content = resp.content.decode()
    if content == '':
        messages.error(request, 'You have to provide a url with text in it to parse!')
        return redirect('index')

    for log_type in types.keys():  # Try all log types
        match_len = len(re.findall(types[log_type], content, re.MULTILINE))
        if match_len > 500:
            messages.error(request, f'Logs with over 500 messages must be processed through the api, found at'
                                    f'{request.META["HTTP_HOST"]}/api!')
            return redirect('index')
        if match_len > 0:
            content = re.sub('\r\n', '\n', content)
            short, created = LogParser(log_type=log_type).create(content, url)
            request.session['cached'] = not created
            return redirect('logs', short_code=short)

    # Mission failed, we'll get em next time
    messages.error(request, 'We can\'t seem to parse that file. Are you sure it\'s a valid log type?')
    return redirect('index')
