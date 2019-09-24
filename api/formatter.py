import base64
import html
import re
from datetime import timedelta, datetime

import demoji
import pytz

from api.emoji import EMOJI_LIST, EMOJI_REGEX, UNICODE_LIST

if not demoji.last_downloaded_timestamp() or datetime.now(pytz.UTC) > \
        (demoji.last_downloaded_timestamp() + timedelta(days=7)):
    demoji.download_codes()

if not demoji._EMOJI_PAT:
    demoji.set_emoji_pattern()


def _encode_codeblock(m):
    encoded = base64.b64encode(m.group(1).encode()).decode()
    return '\x1AM' + encoded + '\x1AM'


def _encode_link(m):
    encoded_1 = base64.b64encode(m.group(1).encode()).decode()
    encoded_2 = base64.b64encode(m.group(2).encode()).decode()
    encoded_3 = ''
    if m.group(3):
        encoded_3 = f'|{base64.b64encode(m.group(5).encode()).decode()}'
    return f'\x1AL{encoded_1}|{encoded_2}{encoded_3}\x1AL'


def _encode_url(m):
    encoded = base64.b64encode(m.group(1).encode()).decode()
    return '\x1AU' + encoded + '\x1AU'


def _encode_inline_codeblock(m):
    encoded = base64.b64encode(m.group(2).encode()).decode()
    return '\x1AI' + encoded + '\x1AI'


def _encode_mentions(m):
    encoded = base64.b64encode(m.group(1).encode()).decode()
    return '\x1AD' + encoded + '\x1AD'


def _process_emojis(m):
    if m.group(2) in EMOJI_LIST:
        emoji = EMOJI_LIST[m.group(2)]
        return emoji
    else:
        return m.group(1)


def _process_unicode_emojis(m, emoji_class):
    e = m.group()
    e = re.sub(r'[\U0000FE00-\U0000FE0F]$', '', e)
    title_e = re.sub(r'[\U0001F3FB-\U0001F3FF]$', '', e)
    if not title_e:
        title_e = e
    title = UNICODE_LIST.get(title_e) or demoji._CODE_TO_DESC[title_e]
    codepoint = "-".join(['%04x' % ord(_c) for _c in e]).lstrip('0')
    return fr'<img class="{emoji_class}" title=":{title}:" ' \
        fr'src="https://twemoji.maxcdn.com/2/svg/{codepoint}.svg" alt="{e}">'


def _decode_link(m):
    encoded_1 = base64.b64decode(m.group(1).encode()).decode()
    encoded_2 = base64.b64decode(m.group(2).encode()).decode()
    encoded_3 = ''
    if m.group(3):
        encoded_3 = f' title="{base64.b64decode(m.group(4).encode()).decode()}"'
    return f'<a href="{encoded_2}"{encoded_3}>{encoded_1}</a>'


def _decode_url(m):
    decoded = base64.b64decode(m.group(1).encode()).decode()
    return '<a href="' + decoded + '">' + decoded + '</a>'


def _decode_mentions(m):
    decoded = base64.b64decode(m.group(1).encode()).decode()
    return decoded


def _smart_mention(m, users):
    uid = m.group(2)
    if users and uid in [u['id'] for u in users]:
        user = next(item for item in users if str(item["id"]) == uid)
        return fr'<span class="mention user" title="{uid}">@{user["username"]}</span>'
    return fr'<span class="mention user" title="{uid}">{m.group(1)}</span>'


def _decode_inline_codeblock(m):
    decoded = base64.b64decode(m.group(1).encode()).decode()
    return '<span class="pre pre--inline">' + decoded + '</span>'


def _decode_codeblock(m):
    decoded = base64.b64decode(m.group(1).encode()).decode()
    match = re.match(r'([^`]*?\n)?([\s\S]+)', decoded)
    lang = match.group(1) or ''
    if not lang.strip(' \n\r'):
        lang = 'plaintext'
    else:
        lang = lang.strip(' \n\r')

    result = html.escape(match.group(2))
    return (f'<div class="pre pre--multiline {lang}">{result}'
            '</div>'.replace('\x00', ''))


def format_content_html(content: str, users: dict = None, masked_links: bool = False, newlines: bool = True) -> str:
    # Encode multiline codeblocks (```text```)
    content = re.sub(r'```+((?:[^`]*?\n)?(?:[\s\S]+))\n?```+', _encode_codeblock, content)

    # Encode links
    if masked_links:
        content = re.sub(r'\[(.*?)\]\((.*?)( (&quot;)(.*?)\4|)\)', _encode_link, content)

    # Encode URLs
    content = re.sub(r'(?:<)?(\b(?:(?:https?|ftp|file)://|www\.|ftp\.)(?:\([-a-zA-Z0'
                     r'-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-zA-Z0-9+&@#/%?=~_|!:,.'
                     r'\[\];])*(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-z'
                     r'A-Z0-9+&@#/%=~_|$]))(?:>)?', _encode_url, content)

    # HTML-encode content
    content = html.escape(content)

    # Encode inline codeblocks (`text` or ``text``)
    content = re.sub(r'(``?)([^`]+)\1', _encode_inline_codeblock, content)

    # Encode mentions
    content = re.sub(r'((@everyone)|(@here)|(&lt;@!?(\d+)&gt;)|(&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;)|'
                     r'(@((.{2,32}?)#\d{4}))|(&lt;#\d+&gt;)|(&lt;#(.{1,100}?)&gt;)|(&lt;@&amp;(\d+)&gt;)|'
                     r'(&lt;@&amp;(.{1,100}?)&gt;))', _encode_mentions, content)

    jumbo_pat = fr'&lt;(:.*?:)(\d*)&gt;|&lt;(a:.*?:)(\d*)&gt;|{demoji._EMOJI_PAT.pattern}'
    jumbo = (not re.sub(r'(\s)', '', re.sub(jumbo_pat, '', content))) and (len(re.findall(jumbo_pat, content)) < 28)
    emoji_class = 'emoji emoji--large' if jumbo else 'emoji'

    # Custom emojis (<:name:id>)
    content = re.sub(r'&lt;(:.*?:)(\d*)&gt;', fr'<img class="{emoji_class}" title="\1" src="'
                     fr'https://cdn.discordapp.com/emojis/\2.png" alt="\1">', content)

    # Custom animated emojis (<a:name:id>)
    content = re.sub(r'&lt;(a:.*?:)(\d*)&gt;', fr'<img class="{emoji_class}" title="\1" src="'
                     fr'https://cdn.discordapp.com/emojis/\2.gif" alt="\1">', content)

    # Process emojis (:text:)
    content = re.sub(EMOJI_REGEX, _process_emojis, content)

    # Process unicode emojis
    content = demoji.replace(content, lambda m: _process_unicode_emojis(m, emoji_class))

    # Process block quotes (> text or >>> te\ntx)
    content = re.sub(r'^&gt; (.+)$|^(?:&gt;){3} ([\S\s]+)$', r'<blockquote>\1\2</blockquote>', content)

    # Process bold (**text**)
    content = re.sub(r'\*\*((?:\\[\s\S]|[^\\])+?)\*\*(?!\*)', r'<b>\1</b>', content)

    # Process underline (__text__)
    content = re.sub(r'__((?:\\[\s\S]|[^\\])+?)__(?!_)', r'<u>\1</u>', content)

    # Process italic (*text* or _text_)
    content = re.sub(r'\b_((?:__|\\[\s\S]|[^\\_])+?)_\b|\*(?=\S)((?:\*\*|\\[\s\S]|\s+(?:\\[\s\S]|[^\s*\\]|\*\*)|'
                     r'[^\s*\\])+?)\*(?!\*)', r'<i>\1\2</i>', content)

    # Process strike through (~~text~~)
    content = re.sub(r'~~(?=\S)((?:\\[\s\S]|~(?!~)|[^\s\\~]|\s+(?!~~))+?)~~', r'<s>\1</s>', content)

    # Decode and process links
    if masked_links:
        # Potential bug, may need to change to: '\x1AL(.*?)\|(.*?)\x1AL'
        content = re.sub('\x1AL(.*?)\\|(.*?)(\\|(.*?)|)\x1AL', _decode_link, content)

    # Decode and process URLs
    content = re.sub('\x1AU(.*?)\x1AU', _decode_url, content)

    if newlines:
        # Process new lines
        content = content.replace('\n', '<br>')

    # Nobody said this was gonna be pretty
    spoiler_html = r'<span class="spoiler-box"><span class="spoiler-text">\2</span></span>'

    # Process spoiler (||text||)
    content = re.sub(r'(\|\|)(?=\S)([\S\s]+?)(?<=\S)\1', spoiler_html, content)

    # Decode mentions
    content = re.sub('\x1AD(.*?)\x1AD', _decode_mentions, content)

    # Meta mentions (@everyone)
    content = content.replace('@everyone', '<span class="mentioned mention no-select">@everyone</span>')

    # Meta mentions (@here)
    content = content.replace('@here', '<span class="mentioned mention no-select">@here</span>')

    # User mentions (<@id> and <@!id>)
    content = re.sub(r'(&lt;@!?(\d+)&gt;)', lambda m: _smart_mention(m, users), content)

    # User mentions (@user#discrim)
    content = re.sub(r'@((.{2,32}?)#\d{4})', r'<span class="mention" title="\1">@\2</span>', content)

    # User mentions (<@user#discrim (id)>)
    content = re.sub(r'&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;',
                     r'<span class="mention user" title="\3">@\2</span>', content)

    # Channel mentions (<#id>)
    content = re.sub(r'(&lt;#\d+&gt;)', r'<span class="mention">\1</span>', content)

    # Channel mentions (<#name>)
    content = re.sub(r'(&lt;#(.{1,100}?)&gt;)',
                     r'<span class="mention">#\2</span>', content)

    # Role mentions (<@&id>)
    content = re.sub(r'(&lt;@&amp;(\d+)&gt;)', r'<span class="mention">\1</span>', content)

    # Role mentions (<@&name>)
    content = re.sub(r'(&lt;@&amp;(.{1,100}?)&gt;)',
                     r'<span class="mention" title="Role: \2">@\2</span>', content)

    # Decode and process inline codeblocks
    content = re.sub('\x1AI(.*?)\x1AI', _decode_inline_codeblock, content)

    # Decode and process multiline codeblocks
    content = re.sub('\x1AM(.*?)\x1AM', _decode_codeblock, content)

    return content


# ======================================
#    Stripped Down Version for Embeds
# ======================================

def format_content_html_lite(content: str, users: dict = None, newlines: bool = True) -> str:
    # Encode multiline codeblocks (```text```)
    content = re.sub(r'```+((?:[^`]*?\n)?(?:[\s\S]+))\n?```+', _encode_codeblock, content)

    # Encode URLs
    content = re.sub(r'(\b(?:(?:https?|ftp|file)://|www\.|ftp\.)(?:\([-a-zA-Z0'
                     r'-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-zA-Z0-9+&@#/%?=~_|!:,.'
                     r'\[\];])*(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-z'
                     r'A-Z0-9+&@#/%=~_|$]))', _encode_url, content)

    # HTML-encode content
    content = html.escape(content)

    # Encode inline codeblocks (`text` or ``text``)
    content = re.sub(r'(``?)([^`]+)\1', _encode_inline_codeblock, content)

    # Encode mentions
    content = re.sub(r'((@everyone)|(@here)|(&lt;@!?(\d+)&gt;)|(&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;)|'
                     r'(@((.{2,32}?)#\d{4}))|(&lt;#\d+&gt;)|(&lt;#(.{1,100}?)&gt;)|(&lt;@&amp;(\d+)&gt;)|'
                     r'(&lt;@&amp;(.{1,100}?)&gt;))', _encode_mentions, content)

    # Process emojis (:text:)
    content = re.sub(EMOJI_REGEX, _process_emojis, content)

    # Process unicode emojis
    content = demoji.replace(content, lambda m: _process_unicode_emojis(m, 'emoji'))

    # Process bold (**text**)
    content = re.sub(r'\*\*((?:\\[\s\S]|[^\\])+?)\*\*(?!\*)', r'<b>\1</b>', content)

    # Process underline (__text__)
    content = re.sub(r'__((?:\\[\s\S]|[^\\])+?)__(?!_)', r'<u>\1</u>', content)

    # Process italic (*text* or _text_)
    content = re.sub(r'\b_((?:__|\\[\s\S]|[^\\_])+?)_\b|\*(?=\S)((?:\*\*|\\[\s\S]|\s+(?:\\[\s\S]|[^\s*\\]|\*\*)|'
                     r'[^\s*\\])+?)\*(?!\*)', r'<i>\1\2</i>', content)

    # Process strike through (~~text~~)
    content = re.sub(r'~~(?=\S)((?:\\[\s\S]|~(?!~)|[^\s\\~]|\s+(?!~~))+?)~~', r'<s>\1</s>', content)

    # Decode and process URLs
    content = re.sub('\x1AU(.*?)\x1AU', _decode_url, content)

    if newlines:
        # Process new lines
        content = content.replace('\n', '<br>')

    # Nobody said this was gonna be pretty
    spoiler_html = r'<span class="spoiler-box"><span class="spoiler-text">\2</span></span>'

    # Process spoiler (||text||)
    content = re.sub(r'(\|\|)(?=\S)([\S\s]+?)(?<=\S)\1', spoiler_html, content)

    # Decode mentions
    content = re.sub('\x1AD(.*?)\x1AD', _decode_mentions, content)

    # Meta mentions (@everyone)
    content = content.replace('@everyone', '<span class="mentioned mention no-select">@everyone</span>')

    # Meta mentions (@here)
    content = content.replace('@here', '<span class="mentioned mention no-select">@here</span>')

    # User mentions (<@id> and <@!id>)
    content = re.sub(r'(&lt;@!?(\d+)&gt;)', lambda m: _smart_mention(m, users), content)

    # User mentions (@user#discrim)
    content = re.sub(r'@((.{2,32}?)#\d{4})', r'<span class="mention" title="\1">@\2</span>', content)

    # User mentions (<@user#discrim (id)>)
    content = re.sub(r'&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;',
                     r'<span class="mention user" title="\3">@\2</span>', content)

    # Channel mentions (<#id>)
    content = re.sub(r'(&lt;#\d+&gt;)', r'<span class="mention">\1</span>', content)

    # Channel mentions (<#name>)
    content = re.sub(r'(&lt;#(.{1,100}?)&gt;)',
                     r'<span class="mention">#\2</span>', content)

    # Role mentions (<@&id>)
    content = re.sub(r'(&lt;@&amp;(\d+)&gt;)', r'<span class="mention">\1</span>', content)

    # Role mentions (<@&name>)
    content = re.sub(r'(&lt;@&amp;(.{1,100}?)&gt;)',
                     r'<span class="mention" title="Role: \2">@\2</span>', content)

    # Decode and process inline codeblocks
    content = re.sub('\x1AI(.*?)\x1AI', _decode_inline_codeblock, content)

    # Decode and process multiline codeblocks
    content = re.sub('\x1AM(.*?)\x1AM', _decode_codeblock, content)

    return content
