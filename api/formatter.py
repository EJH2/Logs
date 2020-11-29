import re

import demoji
import dispy_markdown as md
import pendulum

from api.emoji import EMOJI_LIST, UNICODE_LIST

if not demoji.last_downloaded_timestamp() or pendulum.now() > \
        (pendulum.instance(demoji.last_downloaded_timestamp()).add(days=7)):
    demoji.download_codes()

demoji.set_emoji_pattern()
UNICODE_EMOJI_PAT = demoji._EMOJI_PAT.pattern
jumbo_pat = re.compile(fr'<a?:.*?:\d*>|:[\wñ+-]+:|{UNICODE_EMOJI_PAT}')


class BlockQuote(md.classes['block_quote']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag(
            'div', md.html_tag(
                'div', '', {'class': 'blockquoteDivider-2hH8H6'}, state
            ) + md.html_tag(
                'blockquote', output(node['content'], state)
            ), {'class': 'blockquoteContainer-U5TVEi'}, state
        )


class CodeBlock(md.classes['code_block']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag('pre', md.html_tag(
            'code', md.markdown.sanitize_text(node['content']), {
                'class': node['lang'] or 'plaintext'
            }, state
        ), None, state)


class InlineCode(md.classes['inline_code']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag(
            'code', md.markdown.sanitize_text(node['content'].strip()), {'class': 'inline'}, state
        )


class Spoiler(md.classes['spoiler']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag(
            'span', md.html_tag(
                'span', output(node['content'], state), {'class': 'inlineContent-3ZjPuv'}, state
            ), {'class': 'spoilerText-3p6IlD'}, state
        )


class DiscordUser(md.classes['discord_user']):

    @staticmethod
    def html(node, output, state):
        mention = f'@{user["username"]}' if (user := state['users'].get(node['id'])) else f'<@!{node["id"]}>'
        return md.html_tag('span', mention, {'class': 'mention wrapper-3WhCwL mention'}, state)


class DiscordChannel(md.classes['discord_channel']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag('span', f'<#{node["id"]}>', {'class': 'mention wrapper-3WhCwL mention'}, state)


class DiscordRole(md.classes['discord_role']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag('span', f'<@&{node["id"]}>', {'class': 'mention wrapper-3WhCwL mention'}, state)


class DiscordEmoji(md.classes['discord_emoji']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag(
            'img', '', {
                'class': f'{state["emoji_class"]}{" animated" if node["animated"] else ""}',
                'src': f'https://cdn.discordapp.com/emojis/{node["id"]}.{"gif" if node["animated"] else "png"}',
                'alt': f':{node["name"]}:'
            }
        )


class DiscordEveryone(md.classes['discord_everyone']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag(
            'span', '@everyone', {'class': 'mention wrapper-3WhCwL mention'}, state
        )


class DiscordHere(md.classes['discord_here']):

    @staticmethod
    def html(node, output, state):
        return md.html_tag(
            'span', '@here', {'class': 'mention wrapper-3WhCwL mention'}, state
        )


def _parse_emoji(emoji: str):
    title = UNICODE_LIST.get(emoji, demoji.findall(emoji)[emoji])
    if '\u200d' not in emoji:  # If there isn't a zero width joiner, strip out variation selectors
        emoji = re.sub(r'[\U0000FE00-\U0000FE0F]$', '', emoji)
    return {
        'type': 'unicode_emoji',
        'title': title,
        'emoji': emoji
    }


class DiscordTextEmoji(md.markdown.Rule):

    @staticmethod
    def match(*args, **kwargs):
        return md.markdown.any_scope_regex(r'^:([\wñ+-]+):')(*args, **kwargs)

    @staticmethod
    def parse(capture, parse, state):
        if not capture[1] in EMOJI_LIST:
            return {
                'type': 'text',
                'content': capture[0]
            }
        return _parse_emoji(EMOJI_LIST[capture[1]])


class UnicodeEmoji(md.markdown.Rule):

    @staticmethod
    def match(*args, **kwargs):
        return md.markdown.any_scope_regex(f'^(?:{UNICODE_EMOJI_PAT})')(*args, **kwargs)

    @staticmethod
    def parse(capture, parse, state):
        return _parse_emoji(capture[0])

    @staticmethod
    def html(node, output, state):
        if node['title'] in ['registered', 'copyright', 'tm']:
            return node['emoji']
        codepoint = "-".join(['%04x' % ord(_c) for _c in node["emoji"]]).lstrip('0')
        return md.html_tag(
            'img', '', {
                'class': state['emoji_class'],
                'title': f':{node["title"]}:',
                'src': f'https://twemoji.maxcdn.com/2/svg/{codepoint}.svg',
                'alt': node['emoji']
            }, state
        )


rules_discord_only = {
    **md.rules_discord_only,
    'discord_user': DiscordUser(md.rules['discord_user'].order),
    'discord_channel': DiscordChannel(md.rules['discord_channel'].order),
    'discord_role': DiscordRole(md.rules['discord_role'].order),
    'discord_emoji': DiscordEmoji(md.rules['discord_emoji'].order),
    'discord_everyone': DiscordEveryone(md.rules['discord_everyone'].order),
    'discord_here': DiscordHere(md.rules['discord_here'].order),
    'discord_text_emoji': DiscordTextEmoji(md.rules['discord_emoji'].order),
    'unicode_emoji': UnicodeEmoji(md.rules['discord_emoji'].order)
}

# Used for message content
rules = {
    **md.rules,
    'block_quote': BlockQuote(md.rules['block_quote'].order),
    'code_block': CodeBlock(md.rules['code_block'].order),
    'inline_code': InlineCode(md.rules['inline_code'].order),
    'spoiler': Spoiler(md.rules['spoiler'].order),
    **rules_discord_only
}

# Used for webhook messages, embed description, embed field values
rules_embed = {**md.rules_embed, **rules}
# Used for embed title and field names
rules_embed_lite = rules_embed.copy()
del rules_embed_lite['code_block']
del rules_embed_lite['br']
del rules_embed_lite['discord_user']
del rules_embed_lite['discord_channel']
del rules_embed_lite['discord_role']

parser = md.markdown.parser_for(rules)
html_output = md.markdown.output_for(rules, 'html')
parser_embed = md.markdown.parser_for(rules_embed)
html_output_embed = md.markdown.output_for(rules_embed, 'html')
parser_embed_lite = md.markdown.parser_for(rules_embed_lite)
html_output_embed_lite = md.markdown.output_for(rules_embed_lite, 'html')


def to_html(source: str, options: dict = None):
    options = {
        'embed': False,
        'escape_html': True,
        'users': {},
        **(options if options else {})
    }

    _parser = parser
    _html_output = html_output
    if options['embed']:
        _parser = parser_embed
        _html_output = html_output_embed
        if options['embed'] == 'lite':
            _parser = parser_embed_lite
            _html_output = html_output_embed_lite

    state = {
        'inline': True,
        'in_quote': False,
        'in_emphasis': False,
        'escape_html': options['escape_html'],
        'emoji_class': 'emoji',
        'users': options['users'],
        'css_module_names': options.get('css_module_names')
    }

    if not options['embed']:
        jumbo = (not re.sub(r'(\s)', '', jumbo_pat.sub('', source))) and (len(jumbo_pat.findall(source)) < 28)
        state['emoji_class'] = 'emoji jumboable' if jumbo else 'emoji'

    return _html_output(_parser(source, state), state)
