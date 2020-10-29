from django.conf import settings

DISCORD_TOKEN = getattr(settings, 'LOG_DISCORD_TOKEN', None)

DISCORD_API_URL = 'https://discordapp.com/api/v7/users'

DISCORD_HEADERS = {'Authorization': DISCORD_TOKEN}

rowboat_re = r'(?P<time>(?:[\d-]+) (?:[\d:.]+)) \((?P<mid>[\d]{16,18}) \/ (?P<gid>[\d]{16,18}) \/ (?P<uid>[\d]' \
             r'{16,18})\) (?P<uname>.*?)#(?P<disc>\d{4}): (?P<content>[\S\s]*?)? \((?P<attach>(?:http(?:|s):.*))?\)$'

rosalina_bottings_re = r'(?P<time>(?:[\d-]{10})T(?:[\d:.]{8,15}))(?:\+[\d:]{5}|Z) \| (?P<gname>.*?)\[(?P<gid>\d{16,' \
                       r'18})\] \|  (?P<cname>[\w-]{1,100})\[(?P<cid>\d{16,18})\] \| (?P<uname>.*?)\[(?P<uid>\d{16,' \
                       r'18})\] \| said: (?P<content>[\S\s]*?)(?:\nAttachment: (?P<attach>(?:http(?:|s):.*)))?\nMess' \
                       r'age ID: (?P<mid>\d{16,18})$'

giraffeduck_re = r'\[(?P<time>[\d\-\ \:]{19})\] \((?P<mid>\d{16,18})\) (?P<uname>.*?)#(?P<disc>\d{4}) : (?P<content>' \
                 r'[\S\s]*?)? \| Attach: (?P<attach>(?:http(?:|s):.*))? \| RichEmbed: (?:null|(?P<embeds>.*))$'

auttaja_re = r'\[(?P<time>[\w :]{24,25})\] \((?P<uname>.*?)#(?P<disc>\d{4}) - (?P<uid>\d{16,18})\) \[(?P<mid>\d{16,18' \
             r'})\]: (?P<content>[\S\s]*?)(?: (?P<attach>(?:http(?:|s):.*))?)?$'

logger_re = r'(?P<uname>.*?)#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) \| \((?P<avatar>(?:https://(?:cdn\.)?discordapp\.' \
            r'com/(?:avatars/\d{16,18}|assets|embed/avatars)/\w+\.\w{3,4}(?:\?[\w=]+)?))\) \| (?P<time>[\w :-]{33}) ' \
            r'\([\w ]+\): (?P<content>[\S\s]*?) \| (?P<embeds>(?:{\"embeds\": \[.*?))? \| (?: =====> Attachment:.*?:' \
            r'(?P<attach>(?:http(?:|s):.*)))?$'

sajuukbot_re = r'\[(?P<time>[\w :.-]{26})\] (?P<uname>.*?)#(?P<disc>\d{4}) \((?P<mid>[\d]{16,18}) \/ (?P<uid>[\d]' \
               r'{16,18}) \/ (?P<cid>[\d]{16,18})\): (?P<content>[\S\s]*?)(?: \((?P<attach>(?:http(?:|s):.*))\))?'

vortex_re = r'\[(?P<time>[\w, :]{28,29})\] (?P<uname>.*?)#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) : (?P<content>[\S\s' \
            r']+?)?(?: ?(?P<attach>(?:http(?:|s):.*)))?$'

gearbot_re = r'(?P<time>[\w\-. :]{26}) (?P<gid>\d{16,18}) - (?P<cid>\d{16,18}) - (?P<mid>\d{16,18}) \| (?P<uname>.*?' \
              r')#(?P<disc>\d{4}) \((?P<uid>\d{16,18})\) \| (?P<content>[\S\s]*?)? \|(?: ?(?P<attach>(?:http(?:|s):.*' \
              r'))?)?$'

capnbot_re = r'(?P<time>[\d\-\: \.]{19,26}) \((?P<mid>[\d]{16,18}) \/ (?P<gid>[\d]{16,18}) \/ (?P<uid>[\d]{16,18})\) ' \
             r'\((?P<avatar>(?:https://(?:cdn\.)?discordapp\.com/(?:avatars/\d{16,18}|assets|embed/avatars)/\w+\.\w{3' \
             r',4}(?:\?[\w=]+)?))\) (?P<uname>.*?)#(?P<disc>\d{4}): (?P<content>[\S\s]*?)? \| (?P<attach>(?:http(?' \
             r':|s):.*))? \| (?P<embeds>(?:{\"embeds\": \[).*?)?$'

modmailbot_re = r'\[(?P<time>[\d :-]{19})\](?:(?: \[(?:(?:(?:FROM|TO) USER)|CHAT|COMMAND)\]) \[(?P<uname>.*?)' \
                r'(?:#(?P<disc>\d{4}))?\]( \(Anonymous\) [^:]+?:)? (?P<content>[\S\s]*?)(?:\n{2}\*\*' \
                r'Attachment:\*\* (?P<attach>(?:http(?:|s):.*)))?$| (?P<bcontent>[^\n]+))'

invite_deleter_re = r'\[(?P<gid>[\d]{16,18})-(?P<cid>[\d]{16,18})-(?P<uid>[\d]{16,18})\] (?P<uname>.*?)#' \
                    r'(?P<disc>\d{4}): (?P<content>[\S\s]*?)?$'

attachment_re = r'(?:http(?:s|):\/\/)(?:images-ext-\d|cdn|media).discordapp\.(?:com|net)\/(?:attachments(?:\/\d{16,18' \
                r'}){2}|external\/[^\/]+)\/(?P<filename>.*)'

regexps = {
    'auttaja': auttaja_re,
    'capnbot': capnbot_re,
    'gearbot': gearbot_re,
    'giraffeduck': giraffeduck_re,
    'invite_deleter': invite_deleter_re,
    'logger': logger_re,
    'modmailbot': modmailbot_re,
    'rowboat': rowboat_re,
    'rosalina_bottings': rosalina_bottings_re,
    'sajuukbot': sajuukbot_re,
    'vortex': vortex_re,
}

types = {
    'auttaja': 'Auttaja',
    'capnbot': 'CapnBot',
    'gearbot': 'GearBot',
    'giraffeduck': 'GiraffeDuck',
    'invite_deleter': 'Invite Deleter',
    'logger': 'Logger',
    'modmailbot': 'ModMailBot',
    'rosalina_bottings': 'Rosalina Bottings',
    'rowboat': 'Rowboat',
    'sajuukbot': 'SajuukBot',
    'vortex': 'Vortex'
}

rowboat_types = {
    'dashboard.aperturebot.science': (
        'aperture', 'Aperture'
    ),
    'flyg.farkasdev.com': (
        'flygbåt', 'Flygbåt'
    ),
    'mod.warframe.gg': (
        'heimdallr', 'Heimdallr'
    ),
    'jetski.ga': (
        'jetski', 'Jetski'
    ),
    'jake.dooleylabs.com': (
        'lmg_showboat', 'LMG Showboat'
    ),
    'rawgo.at': (
        'rawgoat', 'Rawgoat'
    ),
    'row.swvn.io': (
        'speedboat', 'Speedboat'
    )
}
