import pendulum
import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404, redirect
from itsdangerous import BadSignature
from sentry_sdk import capture_exception

from api.consts import all_types, task_messages
from api.models import Log
from api.objects import LogRenderer, LiteLogRenderer
from api.permissions import filter_view_queryset
from api.utils import signer
from api.v1.parser import create_log
from web.forms import LogCreateForm
from web.parser import create_preview, save_preview


# Create your views here.
def index(request):
    return render(request, 'discord_logview/index.html', context={'iso': pendulum.now().isoformat()})


@login_required
def new(request):
    if request.method == 'POST':
        if (form := LogCreateForm(request.POST, request.FILES, user=request.user)).is_valid():
            if form.cleaned_data.get('file'):
                content = form.cleaned_data['file'].read()
                if isinstance(content, bytes):
                    content = content.decode()
            else:
                content = requests.get(form.cleaned_data['url']).text
            data = {
                'content': content,
                'log_type': form.cleaned_data['type'],
                'expires': form.cleaned_data['expires'],
                'privacy': form.cleaned_data['privacy'],
                'guild': form.cleaned_data['guild']
            }
            if request.POST['submit_type'] == 'Convert':
                log = create_log(**data, owner=request.user)
                return redirect('log-html', pk=log.pk)
            try:
                data = create_preview(**data)
            except IndexError as e:
                form.add_error('type', str(e))
            else:
                request.session[data['uuid']] = data
                return redirect('log-preview-html', pk=data['uuid'])
    else:
        form = LogCreateForm(user=request.user)
    return render(request, 'discord_logview/new.html', context={
        'form': form,
        'iso': pendulum.now().isoformat()
    })


def _get_log(request, pk):
    return get_object_or_404(filter_view_queryset(request, Log.objects.all()), pk=pk)


def _paginate_logs(msgs, data):
    if (paginator := Paginator(msgs, 50)).num_pages > 1:
        data['chunked'] = True
    try:
        msg_page = paginator.page(data.pop('page'))
    except PageNotAnInteger:
        msg_page = paginator.page(1)
    except EmptyPage:
        msg_page = paginator.page(paginator.num_pages)
    data['page'] = msg_page
    return data


def log_html(request, pk):
    log = _get_log(request, pk)

    if not log.pages.count():
        task_data = log.data.get('tasks')
        return render(request, 'discord_logview/loading.html', context={
            'task_ids': list(zip(task_data, task_messages[-len(task_data):])),
            'iso': pendulum.now().isoformat()
        })

    data = {'uuid': log.uuid}
    page = data['page'] = request.GET.get('page')
    msgs = [msg for msgs in [p.messages for p in log.pages.order_by('index')] for msg in msgs]
    data = _paginate_logs(msgs, data)
    if page:
        if not request.is_ajax():
            return redirect('log-html', pk=pk)
        return render(request, 'discord_logview/messages.html', context={'log': LiteLogRenderer(data)})

    if log.expires:
        if log.expires < pendulum.now():
            log.delete()
            raise Http404
        messages.info(request,
                      f'This log will expire on <time datetime="{log.expires.isoformat()}">'
                      f'{log.expires.strftime("%A, %B %d, %Y at %H:%M:%S UTC")}</time>')

    data = {**data, 'created': log.created, 'users': log.users, 'raw_content': log.content, 'raw_type': log.type,
            'type': all_types.get(log.type), 'user_id': None,
            'delete_token': signer.dumps(f'log.{pk}.{pendulum.now().isoformat()}') if log.owner == request.user
            else None,
            'total_messages': len(msgs)}

    return render(request, 'discord_logview/logs.html', context={'log': LogRenderer(data)})


def log_raw(request, pk):
    log = _get_log(request, pk)

    return render(request, 'discord_logview/lograw.html', context={'content': log.content, 'log': {'type': log.type}})


def log_export(request, pk):
    log = _get_log(request, pk)

    data = {'uuid': log.uuid, 'created': log.created, 'users': log.users, 'raw_content': log.content,
            'raw_type': log.type, 'type': all_types.get(log.type), 'user_id': None}

    msgs = [msg for msgs in [p.messages for p in log.pages.order_by('index')] for msg in msgs]
    data['total_messages'] = len(msgs)
    data['messages'] = msgs
    return render(request, 'discord_logview/logs.html', context={'log': LogRenderer(data), 'export': True})


@login_required
def log_delete(request, pk):
    if 'token' not in request.GET:
        return handle400(request, exception='Token not included in request!')
    try:
        delete_type, token_pk, _ = signer.loads(request.GET['token']).split('.', 2)
    except BadSignature:
        return handle400(request, exception='Invalid delete token!')
    if pk != token_pk:
        return handle400(request, exception='Invalid delete token!')
    if delete_type == 'preview':
        if request.session.get(pk):
            del request.session[pk]
            messages.add_message(request, messages.SUCCESS, 'Preview has been successfully deleted!')
            return redirect('index')
        else:
            raise Http404
    else:
        if (log := get_object_or_404(Log, pk=pk)).owner == request.user:
            log.delete()
        messages.add_message(request, messages.SUCCESS, 'Log has been successfully deleted!')
        return redirect('index')


@login_required
def log_preview_html(request, pk):
    if not (session_data := request.session.get(pk)):
        raise Http404

    data = {'uuid': session_data['uuid']}
    page = data['page'] = request.GET.get('page')
    msgs = session_data['data']['messages']
    data = _paginate_logs(msgs, data)
    if page:
        if not request.is_ajax():
            return redirect('log-preview-html', pk=pk)
        return render(request, 'discord_logview/messages.html', context={'log': LiteLogRenderer(data)})

    data = {**data, 'created': pendulum.now(), 'users': session_data['data']['users'],
            'raw_content': session_data['content'], 'raw_type': session_data['type'],
            'type': all_types.get(session_data['type']), 'user_id': None, 'is_preview': True,
            'delete_token': signer.dumps(f'preview.{pk}.{pendulum.now().isoformat()}'), 'total_messages': len(msgs)}

    messages.add_message(request, messages.INFO, 'This is a preview of what your log would look like. This URL cannot '
                                                 'be shared. If you like what you see, simply click the save icon. '
                                                 'If not, click the trash icon.')
    return render(request, 'discord_logview/logs.html', context={'log': LogRenderer(data)})


@login_required
def log_preview_save(request, pk):
    if not (data := request.session.get(pk)):
        raise Http404
    if Log.objects.filter(pk=pk).exists():
        log = Log.objects.get(pk=pk)
    else:
        log = save_preview(data, owner=request.user)
    del request.session[pk]
    return redirect('log-html', pk=log.pk)


@login_required
def log_preview_raw(request, pk):
    if not (data := request.session.get(pk)):
        raise Http404

    return render(request, 'discord_logview/lograw.html', context={
        'content': data['content'], 'log': {'type': data['type']}
    })


@login_required
def log_preview_export(request, pk):
    if not (data := request.session.get(pk)):
        raise Http404

    data = {'uuid': data['uuid'], 'created': pendulum.now(), 'users': data['data']['users'],
            'messages': data['data']['messages'], 'raw_content': data['content'], 'raw_type': data['type'],
            'type': all_types.get(data['type']), 'user_id': None}

    data['total_messages'] = len(data['messages'])
    return render(request, 'discord_logview/logs.html', context={'log': LogRenderer(data), 'export': True})


# ====================================
#            Error Handlers
# ====================================

def handle400(request, *args, **kwargs):
    return render(request, 'error.html', status=400, context={
        'status': 400,
        'subtext': kwargs.pop('exception'),
        'suggestion': 'It looks like you\'ve got some bad data. For your safety and ours, we\'re gonna stop it here. '
                      'If you are the owner of this data, and know it isn\'t bad, come have a '
                      '<a href="https://discord.gg/3X8WwbU">chat</a>'
    })


def handle403(request, *args, **kwargs):
    return render(request, 'error.html', status=403, context={
        'status': 403,
        'suggestion': 'It looks like you don\'t have the right permissions to access this... whatever it may be. '
                      'I don\'t really know, but what I do know is you can\'t see it!'
    })


def handle404(request, *args, **kwargs):
    return render(request, 'error.html', status=404, context={
        'status': 404,
        'suggestion': 'Whatever you were looking for, it looks like it\'s lost. If you know for sure it <i>should</i>'
                      ' exist, contact me on <a href="https://discord.gg/3X8WwbU">Discord</a>. Sorry about that!'
    })


def handle500(request):
    capture_exception()
    return render(request, 'error.html', status=500, context={
        'status': 500,
        'suggestion': 'It looks like something broke on our end, but never fear. We are probably already scrambling to'
                      ' fix it as you read this, and will have it in tip-top shape in no time... hopefully!'
    })
