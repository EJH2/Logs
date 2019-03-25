from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django_logs.parser import *


# Create your views here.
def index(request):
    embed = json.dumps({
        "description": "Heck, even attachments are included...",
        "color": 1362241,
        "footer": {
            "icon_url": "https://cdn.discordapp.com/embed/avatars/1.png",
            "text": ":^)"
        },
        "thumbnail": {
            "url": "https://cdn.discordapp.com/embed/avatars/2.png"
        },
        "image": {
            "url": "https://cdn.discordapp.com/embed/avatars/3.png"
        },
        "author": {
            "name": "Embeds too!",
            "url": "https://discordapp.com",
            "icon_url": "https://cdn.discordapp.com/embed/avatars/4.png"},
        "fields": [
            {
                "name": "🤔",
                "value": "is there anything this can't do?"
            },
            {
                "name": "😱",
                "value": "not really..."
            },
            {
                "name": "🙄",
                "value": "if you find something we don't support, feel free to message <@EJH2#0330 (125370065624236033)"
                         "> on [Discord](https://discordapp.com)!"
            },
            {
                "name": "How do I use this?",
                "value": "Simply go to https://v.ej.gl/view?url=yoururlhere",
                "inline": True
            },
            {
                "name": "What happens then?",
                "value": "You get your own unique log, looking just as cool as this!",
                "inline": True
            }
        ]
    })
    content = f"""[]
[EJH2#0330 (125370065624236033)]
[EJH2#0330 (125370065624236033)]
[]
[]

[0000-00-00 00:00:00] (125370065624236033) EJH2#0330 : Welcome to **Discord Log Viewer!**

Format virtually any log file into an aesthetically pleasing and readable format. Currently, we support:
<:yes:487035217752752129> Emojis :sunglasses:
<:yes:487035217752752129> *Italics* 
<:yes:487035217752752129> **Bold**
<:yes:487035217752752129> __Underline__
<:yes:487035217752752129> ~~Strikethrough~~
<:yes:487035217752752129> `Inline code`
<:yes:487035217752752129> ||spoilers||
<:yes:487035217752752129> ||***__~~`A combination of all of them`~~__***||
<:yes:487035217752752129> ```diff
+ Multi-line code
``` | Attach: https://cdn.discordapp.com/attachments/352443826473795585/557413456442163200/0.png, https://cdn.discordapp.com/attachments/352443826473795585/557034119939358751/gitignore | RichEmbed: {embed}"""

    data = LogParser('giraffeduck').parse(content)
    data['type'] = None
    for msg in data['messages']:
        msg['timestamp'] = None
    data['generated_at'] = None
    return render(request, 'django_logs/logs.html', context={'log_entry': LogEntry(data), 'log_type': None})


def logs(request, short_code, raw=False):
    try:
        log = LogRoute.objects.get(short_code=short_code)
        if raw:
            content = f"<pre>{log.data['raw_content']}</pre>"
            return HttpResponse(content)
        return render(request, 'django_logs/logs.html', context={'log_entry': LogEntry(log.data), 'original_url': log.url,
                                                          'log_type': log.log_type})
    except ObjectDoesNotExist:
        return HttpResponse('Log not found.')


def view(request):
    url = request.GET.get('url', None)
    if url is None or url is '':
        messages.error(request, 'You have to provide a url to parse!')
        return redirect('index')

    resp = requests.get(url)
    assert isinstance(resp, requests.Response)
    content = resp.content.decode()
    if content == '':
        messages.error(request, 'You have to provide a url with text in it to parse!')
        return redirect('index')

    # Cached?
    cached = LogRoute.objects.filter(url=url).exists()
    if cached:  # Cached
        return redirect('logs', short_code=LogRoute.objects.get(url=url).short_code)

    types = {'rowboat': rowboat_re, 'rosalina_bottings': rosalina_bottings_re, 'giraffeduck': giraffeduck_re,
             'auttaja': auttaja_detect_re, 'logger': logger_detect_re, 'sajuukbot': sajuukbot_detect_re}

    for log_type in types.keys():  # Try all log types
        if len(re.findall(types[log_type], content)) > 0:
            short = LogParser(log_type=log_type).create(content, url)
            return redirect('logs', short_code=short)

    # Mission failed, we'll get em next time
    return HttpResponse('We can\'t seem to parse that file. Are you sure it\'s a valid log type?', 404)


def handler404(request):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
