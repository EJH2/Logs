import base64
import html
import re

import emoji_unicode

from django_logs.emoji import EMOJI_LIST, UNICODE_LIST, EMOJI_REGEX


def format_content_html(content: str, masked_links: bool = False) -> str:
    # HTML-encode content

    def encode_codeblock(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AM' + encoded + '\x1AM'

    # Encode multiline codeblocks (```text```)
    content = re.sub(r'```+((?:[^`]*?\n)?(?:[^`]+))\n?```+',
                     encode_codeblock,
                     content)

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
                     r'-9+&@#/%?=~_|!:,\.\[\];]*\)|[-a-zA-Z0-9+&@#/%?=~_|!:,\.'
                     r'\[\];])*(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,\.\[\];]*\)|[-a-z'
                     r'A-Z0-9+&@#/%=~_|$]))(?:>)?', encode_url, content)

    content = html.escape(content)

    def encode_inline_codeblock(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AI' + encoded + '\x1AI'

    # Encode inline codeblocks (`text`)
    content = re.sub(r'`([^`]+)`', encode_inline_codeblock, content)

    def is_jumboable(pattern, text):
        return (not re.sub(r'(\s)', '', re.sub(pattern, '', text))) and (len(re.findall(pattern, text)) < 28)

    def process_unicode_emojis(m, text):
        e = emoji_unicode.Emoji(unicode=m.group('emoji'))
        emoji_class = 'emoji emoji--large' if is_jumboable(EMOJI_REGEX, text) else 'emoji'
        return fr'<img class="{emoji_class}" title="{UNICODE_LIST[m.group(1)].replace("_", " ")}" ' \
               fr'src="https://twemoji.maxcdn.com/2/svg/{e.code_points}.svg" alt="{e.unicode}">'

    # Process unicode emojis
    content = re.sub(EMOJI_REGEX, lambda m: process_unicode_emojis(m, content), content)

    def process_emojis(m, text):
        if m.group(3).startswith('skin-tone-'):
            return ''
        if m.group(3) in EMOJI_LIST:
            emoji = EMOJI_LIST[m.group(3)]
            codepoint = "-".join(['%04x' % ord(_c) for _c in emoji])
            emoji_class = 'emoji emoji--large' if is_jumboable(r'(\:)([\w-]+?)\1', text) else 'emoji'
            return fr'<img class="{emoji_class}" title="{m.group(3).replace("_", " ")}" ' \
                   fr'src="https://twemoji.maxcdn.com/2/svg/{codepoint}.svg" alt="{emoji}">'
        else:
            return m.group(1)

    # Process emojis (:text:)
    content = re.sub(r'((\:)([\w-]+?)\2)', lambda m: process_emojis(m, content), content)

    # Process bold (**text**)
    content = re.sub(r'(\*\*)(?=\S)(.+?[*_]*)(?<=\S)\1', r'<b>\2</b>', content)

    # Process underline (__text__)
    content = re.sub(r'(__)(?=\S)(.+?)(?<=\S)\1', r'<u>\2</u>', content)

    # Process italic (*text* or _text_)
    content = re.sub(r'(\*|_)(?=\S)(.+?)(?<=\S)\1', r'<i>\2</i>', content)

    # Process strike through (~~text~~)
    content = re.sub(r'(~~)(?=\S)(.+?)(?<=\S)\1', r'<s>\2</s>', content)

    def decode_inline_codeblock(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return '<span class="pre pre--inline">' + decoded + '</span>'

    # Decode and process inline codeblocks
    content = re.sub('\x1AI(.*?)\x1AI', decode_inline_codeblock, content)

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

    # Process new lines
    content = content.replace('\n', '<br>')

    # Nobody said this was gonna be pretty
    spoiler_html = r'<span class="chatlog__spoiler-box"><span class="chatlog__spoiler-text">\2</span></span>'

    # Process spoiler (||text||)
    content = re.sub(r'(\|\|)(?=\S)([\S\s]+?)(?<=\S)\1', spoiler_html, content)

    def decode_codeblock(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        match = re.match('^([^`]*?\n)?([^`]+)$', decoded)
        lang = match.group(1) or ''
        if not lang.strip(' \n\r'):
            lang = 'plaintext'
        else:
            lang = lang.strip(' \n\r')

        result = html.escape(match.group(2))
        return (f'<div class="pre pre--multiline {lang}">{result}'
                '</div>')

    # Decode and process multiline codeblocks
    content = re.sub('\x1AM(.*?)\x1AM', decode_codeblock, content)

    # Meta mentions (@everyone)
    content = content.replace('@everyone',
                              '<span class="mention">@everyone</span>')

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

    # Custom emojis (<:name:id>)
    emoji_class = 'emoji emoji--large' if is_jumboable(r'&lt;(:.*?:)(\d*)&gt;', content) else 'emoji'
    content = re.sub(r'&lt;(:.*?:)(\d*)&gt;', fr'<img class="{emoji_class}" title="\1" src="'
                                              fr'https://cdn.discordapp.com/emojis/\2.png" alt="\1">', content)

    # Custom animated emojis (<a:name:id>)
    emoji_class_animated = 'emoji emoji--large' if is_jumboable(r'&lt;(a:.*?:)(\d*)&gt;', content) else 'emoji'
    content = re.sub(r'&lt;(a:.*?:)(\d*)&gt;', fr'<img class="{emoji_class_animated}" title="\1" src="'
                                               fr'https://cdn.discordapp.com/emojis/\2.gif" alt="\1">', content)

    return content


# ======================================
#    Stripped Down Version for Embeds
# ======================================

def format_micro_content_html(content: str) -> str:
    def encode_codeblock(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AM' + encoded + '\x1AM'

    # Encode multiline codeblocks (```text```)
    content = re.sub(r'```+((?:[^`]*?\n)?(?:[^`]+))\n?```+',
                     encode_codeblock,
                     content)

    def encode_url(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AU' + encoded + '\x1AU'

    # Encode URLs
    content = re.sub(r'(\b(?:(?:https?|ftp|file)://|www\.|ftp\.)(?:\([-a-zA-Z0'
                     r'-9+&@#/%?=~_|!:,\.\[\];]*\)|[-a-zA-Z0-9+&@#/%?=~_|!:,\.'
                     r'\[\];])*(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,\.\[\];]*\)|[-a-z'
                     r'A-Z0-9+&@#/%=~_|$]))', encode_url, content)

    content = html.escape(content)

    def encode_inline_codeblock(m):
        encoded = base64.b64encode(m.group(1).encode()).decode()
        return '\x1AI' + encoded + '\x1AI'

    # Encode inline codeblocks (`text`)
    content = re.sub(r'`([^`]+)`', encode_inline_codeblock, content)

    emoji_pattern = re.compile(emoji_unicode.RE_PATTERN_TEMPLATE)

    def process_unicode_emojis(m):
        e = emoji_unicode.Emoji(unicode=m.group('emoji'))
        return fr'<img class="emoji" title="{UNICODE_LIST[m.group(1)].replace("_", " ")}" ' \
               fr'src="https://twemoji.maxcdn.com/2/svg/{e.code_points}.svg" alt="{e.unicode}">'

    # Process unicode emojis
    content = re.sub(emoji_pattern, process_unicode_emojis, content)

    def process_emojis(m):
        if m.group(2).startswith('skin-tone-'):
            return ''
        if m.group(2) in EMOJI_LIST:
            emoji = EMOJI_LIST[m.group(2)]
            codepoint = "-".join(['%04x' % ord(_c) for _c in emoji])
            return fr'<img class="emoji" title="{m.group(2).replace("_", " ")}" ' \
                   fr'src="https://twemoji.maxcdn.com/2/svg/{codepoint}.svg" alt="{emoji}">'
        return f'{m.group(1)}{m.group(2)}{m.group(1)}'

    # Process emojis (:text:)
    content = re.sub(r'(\:)([\w-]+?)\1', process_emojis, content)

    # Process bold (**text**)
    content = re.sub(r'(\*\*)(?=\S)(.+?[*_]*)(?<=\S)\1', r'<b>\2</b>', content)

    # Process underline (__text__)
    content = re.sub(r'(__)(?=\S)(.+?)(?<=\S)\1', r'<u>\2</u>', content)

    # Process italic (*text* or _text_)
    content = re.sub(r'(\*|_)(?=\S)(.+?)(?<=\S)\1', r'<i>\2</i>', content)

    # Process strike through (~~text~~)
    content = re.sub(r'(~~)(?=\S)(.+?)(?<=\S)\1', r'<s>\2</s>', content)

    def decode_inline_codeblock(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return '<span class="pre pre--inline">' + decoded + '</span>'

    # Decode and process inline codeblocks
    content = re.sub('\x1AI(.*?)\x1AI', decode_inline_codeblock, content)

    # Decode and process links
    def decode_url(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        return '<a href="' + decoded + '">' + decoded + '</a>'

    # Decode and process URLs
    content = re.sub('\x1AU(.*?)\x1AU', decode_url, content)

    # Process new lines
    content = content.replace('\n', '<br>')

    # Nobody said this was gonna be pretty
    spoiler_html = r'<span class="chatlog__spoiler-box"><span class="chatlog__spoiler-text">\2</span></span>'

    # Process spoiler (||text||)
    content = re.sub(r'(\|\|)(?=\S)([\S\s]+?)(?<=\S)\1', spoiler_html, content)

    def decode_codeblock(m):
        decoded = base64.b64decode(m.group(1).encode()).decode()
        match = re.match('^([^`]*?\n)?([^`]+)$', decoded)
        lang = match.group(1) or ''
        if not lang.strip(' \n\r'):
            lang = 'plaintext'
        else:
            lang = lang.strip(' \n\r')

        result = html.escape(match.group(2))
        return (f'<div class="pre pre--multiline {lang}">{result}'
                '</div>')

    # Decode and process multiline codeblocks
    content = re.sub('\x1AM(.*?)\x1AM', decode_codeblock, content)

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

    return content
