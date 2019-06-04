import base64
import html
import re
from datetime import timedelta, datetime

import demoji
import pytz

from django_logs.emoji import EMOJI_LIST, EMOJI_REGEX, UNICODE_LIST

if not demoji.last_downloaded_timestamp() or datetime.now(pytz.UTC) > \
        (demoji.last_downloaded_timestamp() + timedelta(days=7)):
    demoji.download_codes()


def format_content_html(content: str, masked_links: bool = False, newlines: bool = True) -> str:
    # HTML-encode content

    def encode_codeblock(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AM' + encoded + '\x1AM'

    # Encode multiline codeblocks (```text```)
    content = re.sub(r'```+((?:[^`]*?\n)?(?:[\s\S]+))\n?```+', encode_codeblock, content)

    # Encode links
    if masked_links:
        def encode_link(m):
            encoded_1 = base64.b64encode(m.group(1).encode()).decode()
            encoded_2 = base64.b64encode(m.group(2).encode()).decode()
            encoded_3 = ''
            if m.group(3):
                encoded_3 = f'|{base64.b64encode(m.group(5).encode()).decode()}'
            return f'\x1AL{encoded_1}|{encoded_2}{encoded_3}\x1AL'

        content = re.sub(r'\[(.*?)\]\((.*?)( (&quot;)(.*?)\4|)\)', encode_link, content)

    def encode_url(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AU' + encoded + '\x1AU'

    # Encode URLs
    content = re.sub(r'(?:<)?(\b(?:(?:https?|ftp|file)://|www\.|ftp\.)(?:\([-a-zA-Z0'
                     r'-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-zA-Z0-9+&@#/%?=~_|!:,.'
                     r'\[\];])*(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-z'
                     r'A-Z0-9+&@#/%=~_|$]))(?:>)?', encode_url, content)

    content = html.escape(content)

    def encode_inline_codeblock(m):
        encoded = base64.b64encode(m.group(2).encode()).decode()
        return '\x1AI' + encoded + '\x1AI'

    # Encode inline codeblocks (`text` or ``text``)
    content = re.sub(r'(``?)([^`]+)\1', encode_inline_codeblock, content)

    def encode_mentions(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AD' + encoded + '\x1AD'

    # Encode mentions
    content = re.sub(r'((@everyone)|(@here)|(&lt;@!?(\d+)&gt;)|(&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;)|'
                     r'(@((.{2,32}?)#\d{4}))|(&lt;#\d+&gt;)|(&lt;#(.{1,100}?)&gt;)|(&lt;@&amp;(\d+)&gt;)|'
                     r'(&lt;@&amp;(.{1,100}?)&gt;))', encode_mentions, content)

    def is_jumboable(pattern, text):
        return (not re.sub(r'(\s)', '', re.sub(pattern, '', text))) and (len(re.findall(pattern, text)) < 28)

    # Custom emojis (<:name:id>)
    _emoji_class = 'emoji emoji--large' if is_jumboable(r'&lt;(:.*?:)(\d*)&gt;', content) else 'emoji'
    content = re.sub(r'&lt;(:.*?:)(\d*)&gt;', fr'<img class="{_emoji_class}" title="\1" src="'
                                              fr'https://cdn.discordapp.com/emojis/\2.png" alt="\1">', content)

    # Custom animated emojis (<a:name:id>)
    _emoji_class_animated = 'emoji emoji--large' if is_jumboable(r'&lt;(a:.*?:)(\d*)&gt;', content) else 'emoji'
    content = re.sub(r'&lt;(a:.*?:)(\d*)&gt;', fr'<img class="{_emoji_class_animated}" title="\1" src="'
                                               fr'https://cdn.discordapp.com/emojis/\2.gif" alt="\1">', content)

    def process_emojis(m):
        if m.group(2) in EMOJI_LIST:
            emoji = EMOJI_LIST[m.group(2)]
            return emoji
        else:
            return m.group(1)

    # Process emojis (:text:)
    content = re.sub(EMOJI_REGEX, process_emojis, content)

    def process_unicode_emojis(m, text):
        e = m.group()
        e = re.sub(r'[\U0000FE00-\U0000FE0F]$', '', e)
        title_e = re.sub(r'[\U0001F3FB-\U0001F3FF]$', '', e)
        if not title_e:
            title_e = e
        title = UNICODE_LIST.get(title_e) or demoji._CODE_TO_DESC[title_e]
        emoji_class = 'emoji emoji--large' if is_jumboable(demoji._EMOJI_PAT, text) else 'emoji'
        codepoint = "-".join(['%04x' % ord(_c) for _c in e]).lstrip('0')
        return fr'<img class="{emoji_class}" title=":{title}:" ' \
            fr'src="https://twemoji.maxcdn.com/2/svg/{codepoint}.svg" alt="{e}">'

    # Process unicode emojis
    content = demoji.replace(content, lambda m: process_unicode_emojis(m, content))

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
        def decode_link(m):
            encoded_1 = base64.b64decode(m.group(1).encode()).decode()
            encoded_2 = base64.b64decode(m.group(2).encode()).decode()
            encoded_3 = ''
            if m.group(3):
                encoded_3 = f' title="{base64.b64decode(m.group(4).encode()).decode()}"'
            return f'<a href="{encoded_2}"{encoded_3}>{encoded_1}</a>'

        # Potential bug, may need to change to: '\x1AL(.*?)\|(.*?)\x1AL'
        content = re.sub('\x1AL(.*?)\\|(.*?)(\\|(.*?)|)\x1AL', decode_link, content)

    def decode_url(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return '<a href="' + decoded + '">' + decoded + '</a>'

    # Decode and process URLs
    content = re.sub('\x1AU(.*?)\x1AU', decode_url, content)

    if newlines:
        # Process new lines
        content = content.replace('\n', '<br>')

    # Nobody said this was gonna be pretty
    spoiler_html = r'<span class="chatlog__spoiler-box"><span class="chatlog__spoiler-text">\2</span></span>'

    # Process spoiler (||text||)
    content = re.sub(r'(\|\|)(?=\S)([\S\s]+?)(?<=\S)\1', spoiler_html, content)

    def decode_mentions(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return decoded

    # Decode mentions
    content = re.sub('\x1AD(.*?)\x1AD', decode_mentions, content)

    # Meta mentions (@everyone)
    content = content.replace('@everyone', '<span class="mention">@everyone</span>')

    # Meta mentions (@here)
    content = content.replace('@here', '<span class="mention">@here</span>')

    # User mentions (<@id> and <@!id>)
    content = re.sub(r'(&lt;@!?(\d+)&gt;)',
                     r'<span class="mention user" title="\2">\1</span>', content)

    # User mentions (<@user#discrim (id)>)
    content = re.sub(r'&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;',
                     r'<span class="mention user" title="\3">@\2</span>', content)

    # User mentions (@user#discrim)
    content = re.sub(r'@((.{2,32}?)#\d{4})',
                     r'<span class="mention" title="\1">@\2</span>', content)

    # Channel mentions (<#id>)
    content = re.sub(r'(&lt;#\d+&gt;)',
                     r'<span class="mention">\1</span>', content)

    # Channel mentions (<#name>)
    content = re.sub(r'(&lt;#(.{1,100}?)&gt;)',
                     r'<span class="mention">#\2</span>', content)

    # Role mentions (<@&id>)
    content = re.sub(r'(&lt;@&amp;(\d+)&gt;)',
                     r'<span class="mention">\1</span>', content)

    # Role mentions (<@&name>)
    content = re.sub(r'(&lt;@&amp;(.{1,100}?)&gt;)',
                     r'<span class="mention" title="Role: \2">@\2</span>', content)

    def decode_inline_codeblock(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return '<span class="pre pre--inline">' + decoded + '</span>'

    # Decode and process inline codeblocks
    content = re.sub('\x1AI(.*?)\x1AI', decode_inline_codeblock, content)

    def decode_codeblock(m):
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

    # Decode and process multiline codeblocks
    content = re.sub('\x1AM(.*?)\x1AM', decode_codeblock, content)

    return content


# ======================================
#    Stripped Down Version for Embeds
# ======================================

def format_micro_content_html(content: str, newlines: bool = True) -> str:
    def encode_codeblock(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AM' + encoded + '\x1AM'

    # Encode multiline codeblocks (```text```)
    content = re.sub(r'```+((?:[^`]*?\n)?(?:[\s\S]+))\n?```+', encode_codeblock, content)

    def encode_url(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AU' + encoded + '\x1AU'

    # Encode URLs
    content = re.sub(r'(\b(?:(?:https?|ftp|file)://|www\.|ftp\.)(?:\([-a-zA-Z0'
                     r'-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-zA-Z0-9+&@#/%?=~_|!:,.'
                     r'\[\];])*(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,.\[\];]*\)|[-a-z'
                     r'A-Z0-9+&@#/%=~_|$]))', encode_url, content)

    content = html.escape(content)

    def encode_inline_codeblock(m):
        encoded = base64.b64encode(m.group(2).encode()).decode()
        return '\x1AI' + encoded + '\x1AI'

    # Encode inline codeblocks (`text` or ``text``)
    content = re.sub(r'(``?)([^`]+)\1', encode_inline_codeblock, content)

    def encode_mentions(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AD' + encoded + '\x1AD'

    # Encode mentions
    content = re.sub(r'((@everyone)|(@here)|(&lt;@!?(\d+)&gt;)|(&lt;@((.{2,32}?)#\d{4}) \((\d+)\)&gt;)|'
                     r'(@((.{2,32}?)#\d{4}))|(&lt;#\d+&gt;)|(&lt;#(.{1,100}?)&gt;)|(&lt;@&amp;(\d+)&gt;)|'
                     r'(&lt;@&amp;(.{1,100}?)&gt;))', encode_mentions, content)

    def process_emojis(m):
        if m.group(2) in EMOJI_LIST:
            emoji = EMOJI_LIST[m.group(2)]
            return emoji
        else:
            return m.group(1)

    # Process emojis (:text:)
    content = re.sub(EMOJI_REGEX, process_emojis, content)

    def process_unicode_emojis(m):
        e = m.group()
        e = re.sub(r'[\U0000FE00-\U0000FE0F]$', '', e)
        title_e = re.sub(r'[\U0001F3FB-\U0001F3FF]$', '', e)
        if not title_e:
            title_e = e
        title = UNICODE_LIST.get(title_e) or demoji._CODE_TO_DESC[title_e]
        codepoint = "-".join(['%04x' % ord(_c) for _c in e]).lstrip('0')
        return fr'<img class="emoji" title=":{title}:" ' \
            fr'src="https://twemoji.maxcdn.com/2/svg/{codepoint}.svg" alt="{e}">'

    # Process unicode emojis
    content = demoji.replace(content, process_unicode_emojis)

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
    def decode_url(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return '<a href="' + decoded + '">' + decoded + '</a>'

    # Decode and process URLs
    content = re.sub('\x1AU(.*?)\x1AU', decode_url, content)

    if newlines:
        # Process new lines
        content = content.replace('\n', '<br>')

    # Nobody said this was gonna be pretty
    spoiler_html = r'<span class="chatlog__spoiler-box"><span class="chatlog__spoiler-text">\2</span></span>'

    # Process spoiler (||text||)
    content = re.sub(r'(\|\|)(?=\S)([\S\s]+?)(?<=\S)\1', spoiler_html, content)

    def decode_mentions(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return decoded

    # Decode mentions
    content = re.sub('\x1AD(.*?)\x1AD', decode_mentions, content)

    # Meta mentions (@everyone)
    content = content.replace('@everyone',
                              '<span class="mention">@everyone</span>')

    # Meta mentions (@here)
    content = content.replace('@here', '<span class="mention">@here</span>')

    # User mentions (<@id> and <@!id>)
    content = re.sub(r'(&lt;@!?(\d+)&gt;)',
                     r'<span class="mention" title="\2">\1</span>', content)

    # User mentions (@user#discrim)
    content = re.sub(r'@((.{2,32}?)#\d{4})',
                     r'<span class="mention" title="\1">@\2</span>', content)

    # Channel mentions (<#id>)
    content = re.sub(r'(&lt;#\d+&gt;)',
                     r'<span class="mention">\1</span>', content)

    # Channel mentions (<#name>)
    content = re.sub(r'(&lt;#(.{1,100}?)&gt;)',
                     r'<span class="mention">#\2</span>', content)

    # Role mentions (<@&id>)
    content = re.sub(r'(&lt;@&amp;(\d+)&gt;)',
                     r'<span class="mention">\1</span>', content)

    # Role mentions (<@&name>)
    content = re.sub(r'(&lt;@&amp;(.{1,100}?)&gt;)',
                     r'<span class="mention" title="Role: \2">@\2</span>', content)

    def decode_inline_codeblock(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return '<span class="pre pre--inline">' + decoded + '</span>'

    # Decode and process inline codeblocks
    content = re.sub('\x1AI(.*?)\x1AI', decode_inline_codeblock, content)

    def decode_codeblock(m):
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

    # Decode and process multiline codeblocks
    content = re.sub('\x1AM(.*?)\x1AM', decode_codeblock, content)

    return content
