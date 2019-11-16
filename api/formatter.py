"""
using code from <https://github.com/kyb3r/modmail-api/blob/8759fa08c6ffb838fa2405b5addb676b9c640b2c/core/formatter.py>
© 2018 Kyber, licensed under MIT
modified by https://github.com/EJH2
© 2019 EJH2
"""

import base64
import html
import re

import demoji
import pendulum

from api.emoji import EMOJI_LIST, EMOJI_REGEX, UNICODE_LIST

if not demoji.last_downloaded_timestamp() or pendulum.now() > \
        (pendulum.instance(demoji.last_downloaded_timestamp()).add(days=7)):
    demoji.download_codes()

demoji.set_emoji_pattern()
# This is taken from the Demoji module, because they decided to make the emoji pattern private
esc = (re.escape(c) for c in sorted(dict(demoji.stream_unicodeorg_emojifile(demoji.URL)), key=len, reverse=True))
UNICODE_EMOJI_PAT = re.compile(r"|".join(esc))


def _encode_codeblock(m):
    return f'\x1AM{base64.b64encode(m.group(1).encode()).decode()}\x1AM'


def _encode_link(m):
    encoded_1 = base64.b64encode(m.group(1).encode()).decode()
    encoded_2 = base64.b64encode(m.group(2).encode()).decode()
    encoded_3 = f'|{base64.b64encode(m.group(5).encode()).decode()}' if m.group(3) else ''
    return f'\x1AL{encoded_1}|{encoded_2}{encoded_3}\x1AL'


def _encode_url(m):
    return f'\x1AU{base64.b64encode(m.group(1).encode()).decode()}\x1AU'


def _encode_inline_codeblock(m):
    return f'\x1AI{base64.b64encode(m.group(2).encode()).decode()}\x1AI'


def _encode_mentions(m):
    return f'\x1AD{base64.b64encode(m.group(1).encode()).decode()}\x1AD'


def _process_emojis(m):
    return EMOJI_LIST[m.group(2)] if m.group(2) in EMOJI_LIST.keys() else m.group(1)


def _process_unicode_emojis(m, emoji_class):
    e = re.sub(r'[\U0000FE00-\U0000FE0F]$', '', m.group())
    title_e = re.sub(r'[\U0001F3FB-\U0001F3FF]$', '', e) or e
    title = UNICODE_LIST.get(title_e, demoji.findall(title_e)[title_e])
    codepoint = "-".join(['%04x' % ord(_c) for _c in e]).lstrip('0')
    return f'<img class="{emoji_class}" title=":{title}:" ' \
        f'src="https://twemoji.maxcdn.com/2/svg/{codepoint}.svg" alt="{e}">'


def _decode_link(m):
    encoded_1 = base64.b64decode(m.group(1).encode()).decode()
    encoded_2 = base64.b64decode(m.group(2).encode()).decode()
    encoded_3 = f' title="{base64.b64decode(m.group(4).encode()).decode()}"' if m.group(3) else ''
    return f'<a href="{encoded_2}"{encoded_3}>{encoded_1}</a>'


def _decode_url(m):
    decoded = base64.b64decode(m.group(1).encode()).decode()
    return f'<a href="{decoded}">{decoded}</a>'


def _decode_mentions(m):
    return base64.b64decode(m.group(1).encode()).decode()


def _smart_mention(m, users):
    uid = m.group(2)
    user = next((item for item in users if str(item['id']) == uid), None)
    if user:
        return f'<span class="mention user" title="{uid}">@{user["username"]}</span>'
    return f'<span class="mention user" title="{uid}">{m.group(1)}</span>'


def _find_id_by_name(m, users):
    name, disc = m.groups()
    user = next((item for item in users if item['username'] == name and item['discriminator'] == disc), None)
    if user:
        return f'<span class="mention user" title="{user["id"]}">@{name}</span>'
    return f'<span class="mention" title="{name}#{disc}">@{name}</span>'


def _decode_inline_codeblock(m):
    return f'<span class="pre pre--inline">{base64.b64decode(m.group(1).encode()).decode()}</span>'


def _decode_codeblock(m):
    decoded = base64.b64decode(m.group(1).encode()).decode()
    match = re.match(r'([^`]*?\n)?([\s\S]+)', decoded)
    lang = (match.group(1) or '').strip(' \n\r') or 'plaintext'
    result = html.escape(match.group(2))
    return (f'<div class="pre pre--multiline {lang}">{result}'
            '</div>'.replace('\x00', ''))


def _format_content(content: str, users: dict = None, newlines: bool = True):
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
    content = re.sub(r'@(.{2,32}?)#(\d{4})', lambda m: _find_id_by_name(m, users), content)

    # User mentions (<@user#discrim (id)>)
    content = re.sub(r'&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;',
                     r'<span class="mention user" title="\3">@\2</span>', content)

    # Channel mentions (<#id>)
    content = re.sub(r'(&lt;#\d+&gt;)', r'<span class="mention">\1</span>', content)

    # Channel mentions (<#name>)
    content = re.sub(r'(&lt;#(.{1,100}?)&gt;)', r'<span class="mention">#\2</span>', content)

    # Role mentions (<@&id>)
    content = re.sub(r'(&lt;@&amp;(\d+)&gt;)', r'<span class="mention">\1</span>', content)

    # Role mentions (<@&name>)
    content = re.sub(r'(&lt;@&amp;(.{1,100}?)&gt;)', r'<span class="mention" title="Role: \2">@\2</span>', content)

    # Decode and process inline codeblocks
    content = re.sub('\x1AI(.*?)\x1AI', _decode_inline_codeblock, content)

    # Decode and process multiline codeblocks
    content = re.sub('\x1AM(.*?)\x1AM', _decode_codeblock, content)

    return content


def format_content(content: str, users: dict = None, masked_links: bool = False, newlines: bool = True) -> str:
    """Format raw text content to recognizable HTML"""

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

    jumbo_pat = fr'&lt;(:.*?:)(\d*)&gt;|&lt;(a:.*?:)(\d*)&gt;|{UNICODE_EMOJI_PAT}'
    jumbo = (not re.sub(r'(\s)', '', re.sub(jumbo_pat, '', content))) and (len(re.findall(jumbo_pat, content)) < 28)
    emoji_class = 'emoji emoji--large' if jumbo else 'emoji'

    # Custom emojis (<:name:id>)
    content = re.sub(r'&lt;(:.*?:)(\d*)&gt;', fr'<img class="{emoji_class}" title="\1" src="'
                     fr'https://cdn.discordapp.com/emojis/\2.png" alt="\1">', content)

    # Custom animated emojis (<a:name:id>)
    content = re.sub(r'&lt;a(:.*?:)(\d*)&gt;', fr'<img class="{emoji_class}" title="\1" src="'
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

    return _format_content(content, users, newlines)


def format_content_lite(content: str, users: dict = None, newlines: bool = True) -> str:
    """Format raw text content to recognizable HTML

    This is designated the lite function because some parts of Discord require special parsing rules.
    """

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

    return _format_content(content, users, newlines)
