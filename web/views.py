import pendulum
import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
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
    return render(request, 'discord_logview/index.html', context={'iso': pendulum.now().isoformat()})


@login_required
def new(request):
    if request.method == 'POST':
        form = LogCreateForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
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
            data = create_preview(**data)
            request.session[data['uuid']] = data
            return redirect('log-preview', pk=data['uuid'])
    else:
        form = LogCreateForm(user=request.user)
    return render(request, 'discord_logview/create_log.html', context={
        'form': form,
        'iso': pendulum.now().isoformat()
    })


def _get_privacy(log, request):
    if log.owner == request.user or request.user.is_staff:
        return
    privacy = log.data.get('privacy')
    if not privacy or privacy[0] in ['public', 'invite']:
        # TODO: Add invite setting logic
        return
    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=%s' % request.path)
    social_user = SocialAccount.objects.filter(user=request.user).first()
    if social_user and social_user.extra_data.get('guilds'):
        if privacy[1] in [g['id'] for g in social_user.extra_data.get('guilds')]:
            if not privacy[0] == 'mods':
                return
            if [g for g in social_user.extra_data.get('guilds') if g['id'] == privacy[1] and
                    bool((g['permissions'] >> 13) & 1)]:
                return
    raise Http404('Log not found!')


def log_html(request, pk):
    log = get_object_or_404(Log, pk=pk)
    error = _get_privacy(log, request)
    if error:
        return error

    if log.data.get('tasks') and not log.pages.count() > 0:
        return render(request, 'discord_logview/loading.html', context={
            'task_ids': list(enumerate(log.data.get('tasks'))),
            'iso': pendulum.now().isoformat()
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
        return redirect('log-html', pk=pk)

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
    error = _get_privacy(log, request)
    if error:
        return error

    return render(request, 'discord_logview/lograw.html', context={'content': log.content, 'log': {'type': log.type}})


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

    data = {'uuid': data['uuid'], 'created': pendulum.now(), 'users': data['data']['users'],
            'messages': data['data']['messages'], 'raw_content': data['content'], 'raw_type': data['type'],
            'type': all_types.get(data['type']), 'user_id': None, 'is_preview': True,
            'delete_token': signer.dumps(f'preview.{pk}')}

    msgs = data['messages']
    data['total_messages'] = len(msgs)
    page = request.GET.get('page')
    if not request.is_ajax() and page:
        return redirect('log-preview', pk=pk)

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

    return render(request, 'discord_logview/lograw.html', context={
        'content': data['content'], 'log': {'type': data['type']}
    })


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
