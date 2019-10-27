import re

rowboat_re = r'(?P<timestamp>(?:[\d-]+) (?:[\d:.]+)) \((?P<message_id>[\d]{16,18}) \/ (?P<guild_id>[\d]{16,18}) \/ ' \
             r'(?P<user_id>[\d]{16,18})\) (?P<username>.*?)#(?P<discriminator>\d{4}): (?P<content>[\S\s]*?)? \(' \
             r'(?P<attachments>(?:http(?:|s):.*))?\)$'

rosalina_bottings_re = r'(?P<timestamp>(?:[\d-]{10})T(?:[\d:.]{8,15}))(?:\+[\d:]{5}|Z) \| (?P<guild_name>.*?)\[(?P' \
                       r'<guild_id>\d{16,18})\] \|  (?P<channel_name>[\w-]{1,100})\[(?P<channel_id>\d{16,18})\] \| ' \
                       r'(?P<username>.*?)\[(?P<user_id>\d{16,18})\] \| said: (?P<content>[\S\s]*?)(?:\nAttachment: ' \
                       r'(?P<attachments>(?:http(?:|s):.*)))?\nMessage ID: (?P<message_id>\d{16,18})$'

auttaja_re = r'\[(?P<timestamp>[\w :]{24,25})\] \((?P<username>.*?)#(?P<discriminator>\d{4}) - (?P<user_id>\d{16,18' \
             r'})\) \[(?P<message_id>\d{16,18})\]: (?P<content>[\S\s]*?)(?: (?P<attachments>(?:http(?:|s):.*))?)?$'

gearbot_re = r'(?P<timestamp>[\w\-. :]{26}) (?P<guild_id>\d{16,18}) - (?P<channel_id>\d{16,18}) - (?P<message_id' \
             r'>\d{16,18}) \| (?P<username>.*?)#(?P<discriminator>\d{4}) \((?P<user_id>\d{16,18})\) \| (?P<content>' \
             r'[\S\s]*?)? \|(?: ?(?P<attachments>(?:http(?:|s):.*))?)?$'

modmailbot_re = r'\[(?P<timestamp>[\d :-]{19})\](?:(?: \[FROM USER\]| \[TO USER\] (?:\(Anonymous\) )?\(.*?\))? ' \
                r'(?P<username>.*?)(?:#(?P<discriminator>\d{4}))?: (?P<content>[\S\s]*?)(?:\n{2}\*\*Attachment:\*\* ' \
                r'.*? \(.*\)\n(?P<attachments>(?:http(?:|s):.*)))?$| (?P<bot_content>[^\n]+))'

vortex_re = r'\[(?P<timestamp>[\w, :]{28,29})\] (?P<username>.*?)#(?P<discriminator>\d{4}) \((?P<user_id>\d{16,18})' \
            r'\) : (?P<content>[\S\s]*?)(?P<attachments>(?:\n(?:http(?:|s):.*)|)*?)$'

regexps = {
    'auttaja': auttaja_re,
    'gearbot': gearbot_re,
    'modmailbot': modmailbot_re,
    'rowboat': rowboat_re,
    'rosalina_bottings': rosalina_bottings_re,
    'vortex': vortex_re
}


_private_types = {
    'giraffeduck': 'GiraffeDuck',
    'logger': 'Logger',
}


_public_types = {
    'auttaja': 'Auttaja',
    'gearbot': 'Gearbot',
    'modmailbot': 'ModMailBot',
    'rosalina_bottings': 'Rosalina Bottings',
    'rowboat': 'Rowboat',
    'vortex': 'Vortex',
}


rowboat_types = {
    'aperture': 'Aperture',
    'heimdallr': 'Heimdallr',
    'jetski': 'Jetski',
    'lmg_showboat': 'LMG Showboat',
    'rawgoat': 'Rawgoat',
    'speedboat': 'Speedboat',
}

all_types = {**_public_types, **_private_types, **rowboat_types}

form_types = {k: all_types[k] for k in sorted({**_public_types, **rowboat_types})}

expiry_times = {
    '10min': 60 * 10,
    '30min': 60 * 30,
    '1hour': 60 * 60,
    '1day': 60 * 60 * 24,
    '1week': 60 * 60 * 24 * 7,
    '2weeks': 60 * 60 * 24 * 14,
    '1month': 60 * 60 * 24 * 30,
    '1year': 60 * 60 * 24 * 365,
    'never': None
}

form_expiry_times = list((k, re.sub(r'(\d+|)(\w+)', lambda m: (m.group(1) + ' ' if m.group(1) else ''
                                                               ) + m.group(2).title(), k)) for k in expiry_times)

form_privacy_types = [
    ('public', 'Public'),
    ('guild', 'Guild Only'),
    ('mods', 'Mods Only'),
    ('invite', 'Invite Only'),
]

privacy_types = [p[0] for p in form_privacy_types]
