import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from itsdangerous import BadSignature
from sentry_sdk import capture_exception

from api.consts import all_types
from api.models import Log
from api.objects import LogRenderer
from api.utils import signer
from api.v1.parser import create_log
from web.forms import LogCreateForm
from web.parser import create_preview, save_preview


# Create your views here.
def index(request):
    return render(request, 'discord_logview/index.html', context={'iso': timezone.now().isoformat()})


@login_required
def new(request):
    if request.method == 'POST':
        form = LogCreateForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            if form.cleaned_data.get('file'):
                content = form.cleaned_data['file'].read()
            else:
                content = requests.get(form.cleaned_data['url']).text
            data = {'content': content, 'log_type': form.cleaned_data['type'], 'expires': form.cleaned_data['expires']}
            if request.POST['submit_type'] == 'Convert':
                log = create_log(**data, owner=request.user)
                return redirect('log-html', pk=log.pk)
            data = create_preview(**data)
            request.session[data['uuid']] = data
            return redirect('log-preview', pk=data['uuid'])
    else:
        form = LogCreateForm(user=request.user)
    return render(request, 'discord_logview/create_log.html', context={
        'form': form,
        'iso': timezone.now().isoformat()
    })


def log_html(request, pk):
    log = get_object_or_404(Log, pk=pk)
    if log.data.get('tasks'):
        return render(request, 'discord_logview/loading.html', context={
            'task_ids': list(enumerate(log.data.get('tasks'))),
            'iso': timezone.now().isoformat()
        })

    data = {'uuid': log.uuid, 'created': log.created, 'users': log.users, 'raw_content': log.content,
            'raw_type': log.type, 'type': all_types.get(log.type), 'user_id': None,
            'delete_token': signer.dumps(f'log.{pk}') if log.owner == request.user else None}

    log_pages = log.pages.order_by('index')
    if log_pages.count() > 1:
        data['chunked'] = True
    msgs = [msg for msgs in [p.messages for p in log_pages] for msg in msgs]
    data['total_messages'] = len(msgs)
    page = request.GET.get('page')
    if not request.is_ajax() and page:
        return redirect('logs-html', pk=pk)

    paginator = Paginator(msgs, 100)
    try:
        msg_page = paginator.page(page)
    except PageNotAnInteger:
        msg_page = paginator.page(1)
    except EmptyPage:
        msg_page = paginator.page(paginator.num_pages)
    data['page'] = msg_page
    data['messages'] = msg_page.object_list
    return render(request, 'discord_logview/logs.html', context={'log': LogRenderer(data)})


def log_raw(request, pk):
    log = get_object_or_404(Log, pk=pk)
    return HttpResponse(f"<pre>{log.content}</pre>")


def log_delete(request, pk):
    if 'token' not in request.GET:
        raise Http404('Token not included in request!')
    try:
        delete_type, _ = signer.loads(request.GET['token']).split('.')
    except BadSignature:
        raise Http404('Invalid delete token!')
    if delete_type == 'preview':
        if request.session.get(pk):
            del request.session[pk]
            messages.add_message(request, messages.SUCCESS, 'Preview has been successfully deleted!')
            return redirect('index')
        else:
            raise Http404('Log cannot be found!')
    else:
        log = get_object_or_404(Log, pk=pk)
        if log.owner == request.user:
            log.delete()
        messages.add_message(request, messages.SUCCESS, 'Log has been successfully deleted!')
        return redirect('index')


def log_preview(request, pk):
    data = request.session.get(pk)
    if not data:
        raise Http404('That log could not be found!')

    data = {'uuid': data['uuid'], 'created': timezone.now(), 'users': data['data']['users'],
            'messages': data['data']['messages'], 'raw_content': data['content'], 'raw_type': data['type'],
            'type': all_types.get(data['type']), 'user_id': None, 'is_preview': True,
            'delete_token': signer.dumps(f'preview.{pk}')}

    msgs = data['messages']
    data['total_messages'] = len(msgs)
    page = request.GET.get('page')
    if not request.is_ajax() and page:
        return redirect('logs-preview', pk=pk)

    paginator = Paginator(msgs, 100)
    if paginator.num_pages > 1:
        data['chunked'] = True
    try:
        msg_page = paginator.page(page)
    except PageNotAnInteger:
        msg_page = paginator.page(1)
    except EmptyPage:
        msg_page = paginator.page(paginator.num_pages)
    data['page'] = msg_page
    data['messages'] = msg_page.object_list
    messages.add_message(request, messages.INFO, 'This is a preview of what your log would look like. This URL cannot '
                                                 'be shared. If you like what you see, simply click the save icon. '
                                                 'If not, click the trash icon.')
    return render(request, 'discord_logview/logs.html', context={'log': LogRenderer(data)})


def log_preview_save(request, pk):
    data = request.session.get(pk)
    if not data:
        raise Http404('That log could not be found!')
    if Log.objects.filter(pk=pk).exists():
        log = Log.objects.get(pk=pk)
    else:
        log = save_preview(data, owner=request.user)
    del request.session[pk]
    return redirect('log-html', pk=log.pk)


def log_preview_raw(request, pk):
    data = request.session.get(pk)
    if not data:
        raise Http404('That log could not be found!')
    return HttpResponse(f"<pre>{data['content']}</pre>")


# ====================================
#            Error Handlers
# ====================================

def handle400(request, exception):
    return render(request, '400.html', status=400)


def handle403(request, exception):
    return render(request, '403.html', status=403)


def handle404(request, exception):
    return render(request, '404.html', status=404)


def handle500(request):
    capture_exception()
    return render(request, '500.html', status=500)
